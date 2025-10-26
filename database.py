# database.py
import asyncpg
from typing import Optional
from config import DATABASE_URL

async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id BIGINT PRIMARY KEY,
            api_key TEXT NOT NULL
        )
    """)
    await conn.close()

async def get_user_api_key(telegram_id: int) -> Optional[str]:
    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow("SELECT api_key FROM users WHERE telegram_id = $1", telegram_id)
    await conn.close()
    return row["api_key"] if row else None

async def register_user(telegram_id: int, api_key: str) -> bool:
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute(
            "INSERT INTO users (telegram_id, api_key) VALUES ($1, $2) "
            "ON CONFLICT (telegram_id) DO UPDATE SET api_key = $2",
            telegram_id, api_key
        )
        await conn.close()
        return True
    except Exception:
        return False