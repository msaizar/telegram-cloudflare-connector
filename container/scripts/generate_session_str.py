#!/usr/bin/env python
from os import system, name
import json

from telethon.sync import TelegramClient
from telethon.sessions import StringSession

from src import env


api_id = env.TELEGRAM_API_ID
api_hash = env.TELEGRAM_API_HASH

if not api_id or not api_hash:
    print("Error: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env.local")
    exit(1)


def clear_screen():
    if name == "nt":
        _ = system("cls")
    else:
        _ = system("clear")


with TelegramClient(StringSession(), api_id, api_hash) as client:
    clear_screen()

    session_str = client.session.save()

    account_details = {"session_str": session_str}

    json_str = json.dumps(account_details, indent=4)
    print(json_str)
