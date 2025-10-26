import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
REPORT_FINANCE_API_KEY = os.getenv("REPORT_FINANCE_API_KEY")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не задан в .env")
if not REPORT_FINANCE_API_KEY:
    raise ValueError("REPORT_FINANCE_API_KEY не задан в .env")

BASE_URL = "https://rest.api.report.finance"
HEADERS = {
    "accept": "application/json",
    "X-API-KEY": REPORT_FINANCE_API_KEY,
    "Content-Type": "application/json"
}


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не задан в .env")

TELEGRAM_ADMIN_IDS = set()
admin_ids_raw = os.getenv("TELEGRAM_ADMIN_IDS", "")
if admin_ids_raw.strip():
    try:
        TELEGRAM_ADMIN_IDS = {int(x.strip()) for x in admin_ids_raw.split(",") if x.strip()}
    except ValueError:
        raise ValueError("Некорректный формат TELEGRAM_ADMIN_IDS")