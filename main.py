import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TELEGRAM_BOT_TOKEN
from handlers import start, expenses
from handlers.admin import router as admin_router
from database import init_db  # ← новое

logging.basicConfig(level=logging.INFO)

async def main():
    await init_db()  # ← создаём таблицу при старте

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(expenses.router)
    dp.include_router(admin_router)  # ← админка
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())