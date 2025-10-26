# handlers/admin.py
from aiogram import Router, types
from aiogram.filters import Command
from config import TELEGRAM_ADMIN_IDS
from database import register_user

router = Router()

@router.message(Command("register"))
async def cmd_register(message: types.Message):
    if message.from_user.id not in TELEGRAM_ADMIN_IDS:
        await message.answer("❌ У вас нет прав администратора.")
        return

    args = message.text.split()
    if len(args) != 3:
        await message.answer("Использование: /register <telegram_id> <api_key>")
        return

    try:
        user_id = int(args[1])
        api_key = args[2].strip()
        if not api_key:
            raise ValueError
    except (ValueError, IndexError):
        await message.answer("Неверный формат. Пример: /register 123456789 abcdef123456")
        return

    success = await register_user(user_id, api_key)
    if success:
        await message.answer(f"✅ Пользователь {user_id} успешно зарегистрирован.")
    else:
        await message.answer("❌ Ошибка при регистрации пользователя.")