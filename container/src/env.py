import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TELEGRAM_API_ID = os.environ.get("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH")
TELEGRAM_SESSION_STR = os.environ.get("TELEGRAM_SESSION_STR")

TIMESCALE_CONNECTION = os.environ.get("TIMESCALE_CONNECTION")

# Rate limiting configuration
MAX_CHANNELS_PER_RUN = int(os.environ.get("MAX_CHANNELS_PER_RUN", "15"))
API_CALL_DELAY = float(os.environ.get("API_CALL_DELAY", "1.5"))
MAX_FLOOD_WAIT = int(os.environ.get("MAX_FLOOD_WAIT", "300"))

# Database configuration
DB_CONNECT_TIMEOUT = int(os.environ.get("DB_CONNECT_TIMEOUT", "10"))
DB_STATEMENT_TIMEOUT = int(os.environ.get("DB_STATEMENT_TIMEOUT", "30000"))

CI = os.environ.get("CI") == "true"
