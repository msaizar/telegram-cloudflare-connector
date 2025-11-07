import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TELEGRAM_API_ID = os.environ.get("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH")
TELEGRAM_SESSION_STR = os.environ.get("TELEGRAM_SESSION_STR")

TIMESCALE_CONNECTION = os.environ.get("TIMESCALE_CONNECTION")

# Database configuration
DB_CONNECT_TIMEOUT = int(os.environ.get("DB_CONNECT_TIMEOUT", "10"))
DB_STATEMENT_TIMEOUT = int(os.environ.get("DB_STATEMENT_TIMEOUT", "30000"))

CI = os.environ.get("CI") == "true"
