# handlers/start.py
from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

router = Router()

MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить расход"), KeyboardButton(text="➕ Добавить приход")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False  # меню всегда видно
)

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я помогу вам внести финансовую операцию.\n"
        "Выберите тип операции:",
        reply_markup=MAIN_MENU
    )