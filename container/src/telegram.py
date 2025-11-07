import env
import logging

from telethon import TelegramClient
from telethon.sessions import StringSession


def get_telegram_client():
    # Validate required environment variables
    if not env.TELEGRAM_API_ID:
        raise ValueError("TELEGRAM_API_ID environment variable is required")
    if not env.TELEGRAM_API_HASH:
        raise ValueError("TELEGRAM_API_HASH environment variable is required")
    if not env.TELEGRAM_SESSION_STR:
        raise ValueError("TELEGRAM_SESSION_STR environment variable is required")

    # Validate and convert API ID to integer
    try:
        api_id = int(env.TELEGRAM_API_ID)
    except (ValueError, TypeError) as e:
        raise ValueError(f"TELEGRAM_API_ID must be an integer, got: {env.TELEGRAM_API_ID}") from e

    string_session = StringSession(env.TELEGRAM_SESSION_STR)
    logging.info("Creating Telegram client")

    return TelegramClient(
        session=string_session, api_id=api_id, api_hash=env.TELEGRAM_API_HASH
    )
