import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenSea API configuration
API_KEY = os.getenv("OPENSEA_API_KEY")

# Discord webhook URL for sending notifications
WEBHOOK = os.getenv("DISCORD_WEBHOOK")

# Comma-separated list of OpenSea collection slugs to track
COLLECTIONS_RAW = os.getenv("COLLECTIONS", "")
COLLECTIONS = [x.strip() for x in COLLECTIONS_RAW.split(",") if x.strip()]

# Time interval (in seconds) between checks
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "15"))

# State storage file
STATE_FILE = os.getenv("STATE_FILE", "state.json")

# Starting point for monitoring (e.g., 'today', 'now', Unix timestamp, ISO timestamp, or empty)
def parse_start_time(val):
    if not val:
        return None
    val = val.strip().lower()
    if val in ("latest", "now"):
        return int(datetime.now(timezone.utc).timestamp())
    if val == "today":
        # Midnight UTC of the current day
        return int(datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    if val == "yesterday":
        # Midnight UTC of yesterday
        from datetime import timedelta
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        return int(yesterday.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    
    # Try parsing as integer (Unix timestamp)
    try:
        return int(val)
    except ValueError:
        pass
    
    # Try parsing as ISO 8601 format
    for fmt in (
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(val, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except ValueError:
            continue
            
    print(f"Warning: Could not parse START_TIME '{val}'. Ignoring start time filter.")
    return None

START_TIME = parse_start_time(os.getenv("START_TIME"))
