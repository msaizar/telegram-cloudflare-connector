#!/usr/bin/env python
import asyncio
import sys
import time

from src.telegram import get_telegram_client
from telethon.tl import functions


async def create_test_channel(title=None, description=None):
    """Create a test Telegram channel with auto-generated unique username

    Args:
        title: Channel title (defaults to 'Test Channel')
        description: Channel description (optional)
    """
    if title is None:
        title = "Test Channel"

    if description is None:
        description = "Test channel for telegram-cloudflare-connector"

    # Generate unique username with timestamp
    username = f"tgcc_test_{int(time.time())}"

    client = get_telegram_client()

    try:
        await client.start()

        result = await client(
            functions.channels.CreateChannelRequest(
                title=title,
                about=description,
                megagroup=False,
            )
        )

        channel = result.chats[0]
        print(f"✓ Created channel: {channel.title}")
        print(f"  Channel ID: {channel.id}")

        # Set the auto-generated username
        try:
            await client(
                functions.channels.UpdateUsernameRequest(
                    channel=channel, username=username
                )
            )

            print(f"✓ Set username: @{username}")
            print(f"  URL: https://t.me/{username}")

            print("\n✓ Channel ready for testing!")
            print(f"\nNext steps:")
            print(f"1. Send test message: ./scripts/send_test_message.py {username}")
            print(f"2. Run connector: curl http://localhost:8080/")
            print(f"3. Check database for messages")

        except Exception as e:
            print(f"✗ Error setting username: {e}")
            print(f"  You can set it manually in Telegram app settings")
            print(f"  Channel ID: {channel.id}")

    finally:
        await client.disconnect()


if __name__ == "__main__":
    # Usage: python create_test_channel.py [title] [description]
    # Examples:
    #   python create_test_channel.py
    #   python create_test_channel.py "My Test Channel"
    #   python create_test_channel.py "My Test Channel" "Custom description"

    title = sys.argv[1] if len(sys.argv) > 1 else None
    description = sys.argv[2] if len(sys.argv) > 2 else None

    asyncio.run(create_test_channel(title, description))
