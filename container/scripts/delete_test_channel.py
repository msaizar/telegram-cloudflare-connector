#!/usr/bin/env python
import asyncio
import sys

from src.telegram import get_telegram_client
from telethon.tl import functions


async def delete_test_channel(username):
    """Delete a Telegram channel by username

    Args:
        username: Channel username (e.g. 'tgcc_test_1234567890' or '@tgcc_test_1234567890')
    """
    # Remove @ if present
    if username.startswith("@"):
        username = username[1:]

    client = get_telegram_client()

    try:
        await client.start()

        # Get the channel entity
        try:
            channel = await client.get_entity(username)
        except Exception as e:
            print(f"✗ Could not find channel @{username}")
            print(f"  Error: {e}")
            return

        # Delete the channel

        try:
            await client(functions.channels.DeleteChannelRequest(channel=channel))

            print(f"✓ Deleted channel: {channel.title}")
            print(f"  Username: @{username}")
            print(f"  Channel ID: {channel.id}")

        except Exception as e:
            print(f"✗ Failed to delete channel @{username}")
            print(f"  Error: {e}")
            print(f"  Note: You must be the creator/owner of the channel to delete it")

    finally:
        await client.disconnect()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./scripts/delete_test_channel.py <channel_username>")
        print("Example: ./scripts/delete_test_channel.py tgcc_test_1234567890")
        print("Example: ./scripts/delete_test_channel.py @tgcc_test_1234567890")
        sys.exit(1)

    username = sys.argv[1]
    asyncio.run(delete_test_channel(username))
