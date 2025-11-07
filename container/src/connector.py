import json
import logging
from asyncio import get_event_loop
from urllib import request
import os
import re
import jsonschema
import asyncio
import env

from jsonschema.exceptions import ValidationError, SchemaError
from bs4 import BeautifulSoup
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.messages import GetHistoryRequest

from timescale import TimescaleClient


class UserNotLoggedIn(Exception):
    pass


STYLE_URL_PATTERN = re.compile(
    r"background-image:\s*url\('([^']{1,500})'\)", re.IGNORECASE
)

MAX_GLUED_TEXT_LENGTH = 20000  # 20KB total for glued messages


class TelegramConnector:
    def __init__(self, timescale: TimescaleClient, telegram: TelegramClient):
        try:
            self.event_loop = get_event_loop()
        except RuntimeError:
            # No event loop in current thread, create a new one
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)

        self.timescale = timescale
        self.telegram = telegram

        current_dir = os.path.realpath(__file__)
        current_dir = os.path.dirname(current_dir)
        schema_file_path = os.path.join(current_dir, "schema/topic_schema_message.json")

        with open(schema_file_path) as schema_file:
            self.schema = json.loads(schema_file.read())

    def _get_last_msg_ids(self):
        sql = """
        SELECT DISTINCT source_channel_id AS channel_id, MAX(CAST(platform_message_id AS INTEGER)) as last_msg_id
        FROM message_feed
        WHERE platform_name = 'telegram'
        GROUP BY source_channel_id;
        """
        try:
            with self.timescale.get_cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()

            if not rows:
                logging.info("No last messages found.")
                return {}

            last_msg_ids = {str(row[0]): int(row[1]) for row in rows}
            return last_msg_ids
        except Exception as e:
            logging.error(f"Failed to fetch last message IDs: {e}")
            return {}

    def _get_file_url_from_web_preview(self, url: str, type: str):
        try:
            # Fetch with timeout to prevent hanging
            with request.urlopen(url, timeout=10) as response:
                web_preview = response.read()

            soup_preview = BeautifulSoup(web_preview, "html.parser")

            if type == "video":
                target_element = soup_preview.find(class_="tgme_widget_message_video")

                if target_element:
                    source = target_element.get("src")
                    if source:
                        return source

            if type == "image":
                target_element = soup_preview.find(
                    class_="tgme_widget_message_photo_wrap"
                )

                if target_element:
                    style = target_element.get("style")
                    if style:
                        match = STYLE_URL_PATTERN.search(style)
                        if match:
                            extracted_url = match.group(1)
                            return extracted_url
                        else:
                            logging.warning("No URL found in style attribute")
                            return None

            if type == "audio":
                target_element = soup_preview.find(name="audio")

                if target_element:
                    source = target_element.get("src")
                    if source:
                        return source

        except Exception as e:
            logging.error(f"Failed to fetch web preview from {url}: {e}")
            return None

    def _get_media_elements(self, entity, item):
        media = []

        if not hasattr(entity, "username") or not entity.username:
            return media

        post_preview = f"https://t.me/{entity.username}/{item.id}?embed=1&mode=tme"

        """
        Image
        """
        if item.photo:
            url = self._get_file_url_from_web_preview(post_preview, "image")
            if url:
                media.append({"id": str(item.photo.id), "type": "image", "url": url})

        """
        Audio
        """
        if item.audio:
            url = self._get_file_url_from_web_preview(post_preview, "audio")
            if url:
                media.append({"id": str(item.audio.id), "type": "audio", "url": url})

        if item.voice:
            url = self._get_file_url_from_web_preview(post_preview, "audio")
            if url:
                media.append({"id": str(item.voice.id), "type": "audio", "url": url})

        """
        Video
        """
        if item.video:
            url = self._get_file_url_from_web_preview(post_preview, "video")
            if url:
                media.append({"id": str(item.video.id), "type": "video", "url": url})

        if item.video_note:
            url = self._get_file_url_from_web_preview(post_preview, "video")
            if url:
                media.append(
                    {"id": str(item.video_note.id), "type": "video", "url": url}
                )

        return media

    async def _process_dialog_message(self, dialog_entity, message_item):
        try:
            source_id = message_item.from_id or message_item.peer_id

            if not source_id:
                return

            source_entity = await self.telegram.get_entity(source_id)
            is_bot_message = (
                getattr(source_entity, "bot", False)
                or getattr(message_item, "via_bot_id", None) is not None
            )

            if is_bot_message:
                return

            message_id = str(message_item.id)
            message_text: str = message_item.message

            if message_text is None:
                return

            source_user_id = str(source_entity.id)
            first_name = getattr(source_entity, "first_name", "")
            last_name = getattr(source_entity, "last_name", "")
            source_user_name = f"{first_name} {last_name}".strip()

            if not source_user_name:
                source_user_name = source_entity.username or dialog_entity.title

            dialog_entity_id = str(dialog_entity.id)

            message_data = {
                "timestamp": message_item.date.isoformat(),
                "message": {"id": message_id, "text": message_text},
                "user": {"id": source_user_id, "name": source_user_name},
                "source": {
                    "account_id": str(self.telegram.api_id),
                    "platform": "telegram",
                    "channel": {"id": dialog_entity_id, "name": dialog_entity.title},
                },
            }

            # Add username URL if present
            if hasattr(dialog_entity, "username") and dialog_entity.username:
                message_data["message"][
                    "url"
                ] = f"https://t.me/{dialog_entity.username}"

            if message_item.geo is not None:
                message_data["geo_coords"] = {
                    "type": "Point",
                    "coordinates": [message_item.geo.long, message_item.geo.lat],
                }

            if message_item.poll is not None:
                message_data["message"]["text"] = message_item.poll.poll.question

            media_elements = self._get_media_elements(dialog_entity, message_item)
            if len(media_elements) > 0:
                message_data["message"]["media"] = media_elements

            jsonschema.validate(instance=message_data, schema=self.schema)

            return message_data

        except ValidationError as validation_error:
            logging.error(
                f"Message validation failed for message ID {message_item.id}: {validation_error}"
            )
        except SchemaError as schema_error:
            logging.error(f"Schema error: {schema_error}")
        except Exception as general_error:
            logging.warning(
                f"Failed to process message {message_item.id}: {general_error}"
            )

    def _glue_same_user_messages(self, messages: list):
        user_messages = {}
        glued_messages = []

        for message in messages:
            user_id = message["user"]["id"]
            channel_id = message["source"]["channel"]["id"]
            referenced_post_id = (
                message["source"].get("referenced_post", {}).get("id", "")
            )
            key = (user_id, channel_id, referenced_post_id)

            if key not in user_messages:
                user_messages[key] = []

            user_messages[key].append(message)

        for key, messages in user_messages.items():
            sorted_messages = sorted(messages, key=lambda x: x["timestamp"])

            texts = [msg["message"]["text"] for msg in sorted_messages]
            glued_text = " ".join(texts)

            if len(glued_text) > MAX_GLUED_TEXT_LENGTH:
                glued_text = glued_text[:MAX_GLUED_TEXT_LENGTH]
                logging.warning(
                    f"Glued text exceeded max length, truncated to {MAX_GLUED_TEXT_LENGTH} chars"
                )

            glued_text_without_unicode = glued_text.encode("ascii", "ignore").decode()
            if len(glued_text_without_unicode) < 20:
                continue

            last_message = sorted_messages[-1]
            last_message["message"]["text"] = glued_text.strip()

            all_media = []

            # Combine media files
            for msg in sorted_messages:
                media = msg["message"].get("media")

                if media:
                    all_media.extend(media)

            if len(all_media) > 0:
                last_message["message"]["media"] = all_media

            glued_messages.append(last_message)

        sorted_glued_messages = sorted(glued_messages, key=lambda x: x["timestamp"])
        return sorted_glued_messages

    async def _get_channel_messages(self):
        channel_messages = []
        last_msg_ids = self._get_last_msg_ids()
        processed_count = 0

        async for dialog in self.telegram.iter_dialogs(archived=False):
            try:
                # Skip user chats
                if dialog.is_user:
                    continue

                # Rate limiting: Stop if max channels reached
                if processed_count >= env.MAX_CHANNELS_PER_RUN:
                    logging.warning(
                        f"Reached max channels limit ({env.MAX_CHANNELS_PER_RUN}). Stopping to prevent rate limit."
                    )
                    break

                entity = dialog.entity
                entity_id = str(entity.id)

                last_msg_id = last_msg_ids.get(entity_id, 0)
                limit_value = 20 if last_msg_id == 0 else 0

                # Skip if the message is not newer than the last processed one
                if dialog.message.id <= last_msg_id:
                    continue

                # Rate limiting: Add delay between API calls
                if processed_count > 0:
                    await asyncio.sleep(env.API_CALL_DELAY)

                logging.info(
                    f"Obtaining chat history for '{entity_id}' - '{dialog.name}'..."
                )

                # Handle FloodWaitError with retry logic
                try:
                    history = await self.telegram(
                        GetHistoryRequest(
                            peer=entity,
                            limit=limit_value,
                            offset_id=0,
                            offset_date=None,
                            add_offset=0,
                            max_id=0,
                            min_id=last_msg_id,
                            hash=0,
                        )
                    )
                except FloodWaitError as flood_error:
                    wait_seconds = flood_error.seconds
                    if wait_seconds > env.MAX_FLOOD_WAIT:
                        logging.error(
                            f"FloodWait too long ({wait_seconds}s > {env.MAX_FLOOD_WAIT}s). Skipping channel."
                        )
                        continue
                    logging.warning(
                        f"FloodWait: Sleeping for {wait_seconds} seconds..."
                    )
                    await asyncio.sleep(wait_seconds)
                    # Retry after waiting
                    history = await self.telegram(
                        GetHistoryRequest(
                            peer=entity,
                            limit=limit_value,
                            offset_id=0,
                            offset_date=None,
                            add_offset=0,
                            max_id=0,
                            min_id=last_msg_id,
                            hash=0,
                        )
                    )

                # Process messages in ascending order
                for item in reversed(history.messages):
                    message = await self._process_dialog_message(entity, item)
                    message and channel_messages.append(message)

                processed_count += 1

            except Exception as err:
                logging.error(f"Error processing dialog '{dialog.name}': {str(err)}")
                continue

        if not channel_messages:
            return

        glued_messages = self._glue_same_user_messages(channel_messages)
        logging.info(
            f"Found {len(channel_messages)} messages, compressed to {len(glued_messages)} messages"
        )

        if not glued_messages:
            return

        self.timescale.insert_messages_batch(glued_messages)

    async def _start(self):
        if not self.telegram.is_connected():
            logging.info("User is not connected. Trying to connect now...")
            await self.telegram.start()

        if not await self.telegram.is_user_authorized():
            raise UserNotLoggedIn

        logging.info("Getting user messages from channels...")
        messages = await self._get_channel_messages()

    def start(self):
        logging.info("Starting telegram connector...")
        self.event_loop.run_until_complete(self._start())
