#!/usr/bin/env python
import asyncio

from src.telegram import get_telegram_client


async def list_channels():
    """List all channels/groups you're a member of"""
    client = get_telegram_client()

    try:
        await client.start()

        print("\nChannels and Groups:")
        print("-" * 80)

        async for dialog in client.iter_dialogs(archived=False):
            # Skip user chats
            if dialog.is_user:
                continue

            entity = dialog.entity
            username = getattr(entity, 'username', None)
            channel_type = "Channel" if dialog.is_channel else "Group"

            if username:
                print(f"{channel_type:8} | @{username:30} | {entity.title}")
            else:
                print(f"{channel_type:8} | (no username)                    | {entity.title}")

        print("-" * 80)

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(list_channels())
