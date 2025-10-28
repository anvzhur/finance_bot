# database.py
import asyncpg
from typing import Optional, Dict, Any, List, Tuple
from config import DATABASE_URL

async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id BIGINT PRIMARY KEY,
            api_key TEXT NOT NULL,
            organisation_name TEXT
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_operations (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            operation_type TEXT NOT NULL CHECK (operation_type IN ('income', 'expense')),
            operation_date DATE NOT NULL
        )
    """)
    await conn.close()

async def get_user_api_key(telegram_id: int) -> Optional[str]:
    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow("SELECT api_key FROM users WHERE telegram_id = $1", telegram_id)
    await conn.close()
    return row["api_key"] if row else None

async def get_user_info(telegram_id: int) -> Optional[Dict[str, Any]]:
    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow(
        "SELECT api_key, organisation_name FROM users WHERE telegram_id = $1",
        telegram_id
    )
    await conn.close()
    return dict(row) if row else None

async def register_user(telegram_id: int, api_key: str, organisation_name: str = None) -> bool:
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute(
            """
            INSERT INTO users (telegram_id, api_key, organisation_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (telegram_id) DO UPDATE
            SET api_key = $2, organisation_name = $3
            """,
            telegram_id, api_key, organisation_name
        )
        await conn.close()
        return True
    except Exception:
        return False

async def log_simple_operation(telegram_id: int, operation_type: str, operation_date):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        INSERT INTO user_operations (telegram_id, operation_type, operation_date)
        VALUES ($1, $2, $3)
    """, telegram_id, operation_type, operation_date)
    await conn.close()

async def get_all_operations() -> List[Tuple[int, str, str]]:
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch("""
        SELECT telegram_id, operation_type, operation_date::TEXT
        FROM user_operations
        ORDER BY operation_date DESC, id DESC
    """)
    await conn.close()
    return [(r["telegram_id"], r["operation_type"], r["operation_date"]) for r in rows]