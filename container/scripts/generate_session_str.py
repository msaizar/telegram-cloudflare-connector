from os import system, name
import getpass
import json

from telethon.sync import TelegramClient
from telethon.sessions import StringSession


api_id = getpass.getpass("Enter your api_id: ")
api_hash = getpass.getpass("Enter your api_hash: ")


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
