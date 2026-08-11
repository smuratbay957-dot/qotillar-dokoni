import os
from pathlib import Path

from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent

load_dotenv(BASE / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
START_BALANCE = 1000
WEB_URL = os.getenv("WEB_URL", "http://127.0.0.1:5000").strip()
ADMIN_ID = os.getenv("ADMIN_ID", "").strip()
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "").strip()
BRIDGE_KEY = os.getenv("BRIDGE_KEY", "CHANGE_ME_BRIDGE_KEY").strip()
