# handlers/start.py
from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from config import TELEGRAM_ADMIN_IDS

router = Router()

def get_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="➕ Добавить расход"), KeyboardButton(text="➕ Добавить приход")]
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="👤 Админка")])
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False
    )

@router.message(Command("start"))
async def cmd_start(message: Message):
    is_admin = message.from_user.id in TELEGRAM_ADMIN_IDS
    await message.answer(
        "Привет! Я помогу вам внести финансовую операцию.\n"
        "Выберите тип операции:",
        reply_markup=get_main_menu(is_admin)
    )