# handlers/admin.py
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import TELEGRAM_ADMIN_IDS
from database import register_user, get_all_operations
import csv
import io

router = Router()

class AdminMenu(StatesGroup):
    main = State()

class RegisterForm(StatesGroup):
    waiting_for_telegram_id = State()
    waiting_for_api_key = State()
    waiting_for_organisation_name = State()

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

ADMIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Зарегистрировать пользователя")],
        [KeyboardButton(text="📊 Выгрузить статистику (CSV)")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

@router.message(F.text == "👤 Админка")
@router.message(Command("admin"))
async def show_admin_menu(message: types.Message, state: FSMContext):
    if message.from_user.id not in TELEGRAM_ADMIN_IDS:
        await message.answer("❌ У вас нет прав администратора.")
        return
    await state.set_state(AdminMenu.main)
    await message.answer("Панель администратора:", reply_markup=ADMIN_MENU)

@router.message(AdminMenu.main, F.text == "➕ Зарегистрировать пользователя")
async def start_register_flow(message: types.Message, state: FSMContext):
    await message.answer("Введите Telegram ID пользователя:")
    await state.set_state(RegisterForm.waiting_for_telegram_id)

@router.message(AdminMenu.main, F.text == "📊 Выгрузить статистику (CSV)")
async def trigger_stats(message: types.Message, state: FSMContext):
    if message.from_user.id not in TELEGRAM_ADMIN_IDS:
        await message.answer("❌ У вас нет прав администратора.")
        return
    try:
        operations = await get_all_operations()
        if not operations:
            await message.answer("Нет данных об операциях.")
            return
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["telegram_id", "operation_type", "operation_date"])
        writer.writerows(operations)
        csv_data = output.getvalue()
        output.close()
        csv_bytes = io.BytesIO(csv_data.encode("utf-8"))
        csv_bytes.name = "operations.csv"
        await message.answer_document(
            types.BufferedInputFile(csv_bytes.getvalue(), filename="operations.csv"),
            caption="📊 Файл со всеми операциями (только факт: тип, дата, пользователь)."
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при генерации отчёта: {e}")

@router.message(AdminMenu.main, F.text == "⬅️ Назад")
async def back_to_main(message: types.Message, state: FSMContext):
    from handlers.start import get_main_menu
    is_admin = message.from_user.id in TELEGRAM_ADMIN_IDS
    await state.clear()
    await message.answer("Вы вернулись в главное меню.", reply_markup=get_main_menu(is_admin))

@router.message(RegisterForm.waiting_for_telegram_id)
async def process_telegram_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
        await state.update_data(telegram_id=user_id)
        await message.answer("Введите API-ключ Report.Finance:")
        await state.set_state(RegisterForm.waiting_for_api_key)
    except ValueError:
        await message.answer("Неверный формат ID. Введите целое число.")
        return

@router.message(RegisterForm.waiting_for_api_key)
async def process_api_key(message: types.Message, state: FSMContext):
    api_key = message.text.strip()
    if not api_key:
        await message.answer("API-ключ не может быть пустым. Попробуйте снова:")
        return
    await state.update_data(api_key=api_key)
    await message.answer("Введите название организации (или отправьте «-», чтобы пропустить):")
    await state.set_state(RegisterForm.waiting_for_organisation_name)

@router.message(RegisterForm.waiting_for_organisation_name)
async def process_organisation_name(message: types.Message, state: FSMContext):
    org_name = message.text.strip()
    if org_name == "-":
        org_name = None
    data = await state.get_data()
    success = await register_user(data["telegram_id"], data["api_key"], org_name)
    if success:
        await message.answer(
            f"✅ Пользователь {data['telegram_id']} зарегистрирован.\n"
            f"Организация: {org_name or 'не указана'}."
        )
    else:
        await message.answer("❌ Ошибка при регистрации.")
    await state.set_state(AdminMenu.main)
    await message.answer("Панель администратора:", reply_markup=ADMIN_MENU)