#!/usr/bin/env python
import asyncio
import sys
from datetime import datetime

from src.telegram import get_telegram_client


async def send_test_message(target):
    """Send a test message to a channel

    Args:
        target: Channel username (e.g. 'my_test_channel')
    """
    text = f"Test message at {datetime.now()}"

    client = get_telegram_client()

    try:
        await client.start()
        await client.send_message(target, text)
        print(f"✓ Sent test message to {target}")
        print(f"  Message: {text}")

    finally:
        await client.disconnect()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./scripts/send_test_message.py <channel_username>")
        print("Example: ./scripts/send_test_message.py my_test_channel")
        sys.exit(1)

    target = sys.argv[1]
    asyncio.run(send_test_message(target))
