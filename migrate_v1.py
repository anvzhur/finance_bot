# migrate_to_prod.py
import asyncio
import asyncpg
from config import DATABASE_URL

async def migrate():
    conn = await asyncpg.connect(DATABASE_URL)

    print("🔧 Начинаем миграцию базы данных...")

    # 1. Добавляем organisation_name в users
    try:
        await conn.execute("ALTER TABLE users ADD COLUMN organisation_name TEXT;")
        print("✅ Добавлен столбец 'organisation_name' в таблицу 'users'")
    except asyncpg.exceptions.DuplicateColumnError:
        print("ℹ️ Столбец 'organisation_name' уже существует")
    except Exception as e:
        print(f"⚠️ Ошибка при добавлении organisation_name: {e}")

    # 2. Создаём таблицу user_operations
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_operations (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT NOT NULL,
                operation_type TEXT NOT NULL CHECK (operation_type IN ('income', 'expense')),
                operation_date DATE NOT NULL
            )
        """)
        print("✅ Создана таблица 'user_operations'")
    except Exception as e:
        print(f"⚠️ Ошибка при создании user_operations: {e}")

    await conn.close()
    print("✅ Миграция завершена. База готова к работе в продакшене.")

if __name__ == "__main__":
    asyncio.run(migrate())