# handlers/expenses.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from api_client import ReportFinanceAPI
from keyboards import (
    get_project_keyboard,
    get_account_keyboard,
    get_confirmation_keyboard,
    get_organisation_keyboard
)
from handlers.start import MAIN_MENU as main_menu
from database import get_user_api_key
import datetime
import uuid

router = Router()

class OperationForm(StatesGroup):
    choosing_type = State()
    choosing_project = State()
    choosing_organisation = State()
    choosing_account = State()
    entering_amount = State()
    entering_purpose = State()
    confirming = State()


# --- Выбор типа операции ---
@router.message(F.text == "➕ Добавить расход")
async def add_expense_start(message: Message, state: FSMContext):
    api_key = await get_user_api_key(message.from_user.id)
    if not api_key:
        await message.answer("❌ Вы не зарегистрированы. Обратитесь к администратору.")
        return
    await state.update_data(operation_type="expense", direction_id=510, api_key=api_key)
    await _start_operation_flow(message, state)


@router.message(F.text == "➕ Добавить приход")
async def add_income_start(message: Message, state: FSMContext):
    api_key = await get_user_api_key(message.from_user.id)
    if not api_key:
        await message.answer("❌ Вы не зарегистрированы. Обратитесь к администратору.")
        return
    await state.update_data(operation_type="income", direction_id=500, api_key=api_key)
    await _start_operation_flow(message, state)


async def _start_operation_flow(message: Message, state: FSMContext):
    data = await state.get_data()
    api_key = data.get("api_key")
    if not api_key:
        await message.answer("❌ Ошибка: API-ключ не найден.")
        await state.clear()
        return

    api = ReportFinanceAPI(api_key=api_key)
    try:
        projects = await api.fetch_all_projects()
        if not projects:
            await message.answer("Нет доступных проектов.")
            return
        project_map = {p["projectName"]: p["id"] for p in projects}
        await state.update_data(projects=project_map, projects_full=projects)
        await message.answer("Выберите проект:", reply_markup=get_project_keyboard(projects))
        await state.set_state(OperationForm.choosing_project)
    except Exception as e:
        await message.answer(f"❌ Ошибка загрузки проектов: {e}")


# --- Выбор проекта ---
@router.message(OperationForm.choosing_project)
async def process_project_choice(message: Message, state: FSMContext):
    user_data = await state.get_data()
    project_name = message.text
    project_id = user_data["projects"].get(project_name)
    if project_id is None:
        await message.answer("Неверный выбор. Выберите проект из списка.")
        return

    projects_full = user_data.get("projects_full")
    if not projects_full:
        await message.answer("Ошибка: данные о проектах утеряны.")
        await state.clear()
        return

    selected_project = next((p for p in projects_full if p["id"] == project_id), None)
    if not selected_project:
        await message.answer("Ошибка: проект не найден.")
        await state.clear()
        return

    await state.update_data(
        project_id=project_id,
        project_name=project_name
    )

    api_key = user_data["api_key"]
    api = ReportFinanceAPI(api_key=api_key)

    try:
        organisations = await api.fetch_all_organisations()
        if not organisations:
            await message.answer("Нет доступных организаций.")
            await state.clear()
            return
        org_map = {org.get("organisationName") or f"Орг {org['id']}": org["id"] for org in organisations}
        await state.update_data(organisations=org_map, organisations_full=organisations)
        await message.answer("Выберите организацию:", reply_markup=get_organisation_keyboard(organisations))
        await state.set_state(OperationForm.choosing_organisation)
    except Exception as e:
        await message.answer(f"❌ Ошибка загрузки организаций: {e}")
        await state.clear()


# --- Выбор организации ---
@router.message(OperationForm.choosing_organisation)
async def process_organisation_choice(message: Message, state: FSMContext):
    user_data = await state.get_data()
    org_name = message.text
    organisation_id = user_data["organisations"].get(org_name)
    if organisation_id is None:
        await message.answer("Неверный выбор. Выберите организацию из списка.")
        return

    await state.update_data(organisation_id=organisation_id, organisation_name=org_name)

    api_key = user_data["api_key"]
    api = ReportFinanceAPI(api_key=api_key)

    try:
        accounts = await api.fetch_all_accounts()
        if not accounts:
            await message.answer("Нет доступных банковских счетов.")
            await state.clear()
            return
        account_map = {
            f"{a['accountName']} ({a['number'][-4:]})": a["id"]
            for a in accounts
        }
        await state.update_data(accounts=account_map, accounts_full=accounts)
        await message.answer("Выберите счёт:", reply_markup=get_account_keyboard(accounts))
        await state.set_state(OperationForm.choosing_account)
    except Exception as e:
        await message.answer(f"❌ Ошибка загрузки счетов: {e}")
        await state.clear()


# --- Выбор счёта ---
@router.message(OperationForm.choosing_account)
async def process_account_choice(message: Message, state: FSMContext):
    user_data = await state.get_data()
    account_key = message.text
    account_id = user_data["accounts"].get(account_key)
    if account_id is None:
        await message.answer("Неверный выбор. Выберите счёт из списка.")
        return

    account_name = next(
        (a["accountName"] for a in user_data["accounts_full"] if a["id"] == account_id),
        account_key
    )
    await state.update_data(account_id=account_id, account_name=account_name)
    await message.answer("Введите сумму (в рублях):")
    await state.set_state(OperationForm.entering_amount)


# --- Ввод суммы ---
@router.message(OperationForm.entering_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            raise ValueError
        await state.update_data(amount=amount)
        await message.answer("Введите назначение платежа:")
        await state.set_state(OperationForm.entering_purpose)
    except ValueError:
        await message.answer("Введите корректную положительную сумму.")


# --- Ввод назначения ---
@router.message(OperationForm.entering_purpose)
async def process_purpose(message: Message, state: FSMContext):
    await state.update_data(purpose=message.text)
    data = await state.get_data()
    operation_word = "Расход" if data["direction_id"] == 510 else "Приход"
    await message.answer(
        f"Подтвердите ввод:\n"
        f"Тип: {operation_word}\n"
        f"Проект: {data['project_name']}\n"
        f"Организация: {data['organisation_name']}\n"
        f"Счёт: {data['account_name']}\n"
        f"Сумма: {data['amount']} ₽\n"
        f"Назначение: {data['purpose']}",
        reply_markup=get_confirmation_keyboard()
    )
    await state.set_state(OperationForm.confirming)


# --- Подтверждение ---
@router.message(OperationForm.confirming)
async def confirm_operation(message: Message, state: FSMContext):
    if message.text not in ("✅ Да", "❌ Нет"):
        await message.answer("Пожалуйста, используйте кнопки для подтверждения.")
        return

    if message.text == "❌ Нет":
        await state.clear()
        await message.answer("Операция отменена.", reply_markup=main_menu)
        return

    data = await state.get_data()
    api_key = data.get("api_key")
    if not api_key:
        await message.answer("❌ Ошибка: API-ключ не найден. Операция отменена.", reply_markup=main_menu)
        await state.clear()
        return

    api = ReportFinanceAPI(api_key=api_key)
    direction_id = data["direction_id"]
    payment_data = {
        "externalId": str(uuid.uuid4()),
        "accountId": data["account_id"],
        "projectId": data["project_id"],
        "organisationId": data["organisation_id"],
        "paymentDate": datetime.date.today().isoformat(),
        "sourcePaymentSum": data["amount"],
        "paymentSum": 0,
        "sourceCurrencyId": "RUB",
        "paymentPurpose": data["purpose"],
        "comment": "Бот Мое дело",
        "directionId": direction_id,
        "operationTypeId": 411,
        "paymentStatusId": 529,
        "priorityId": 532,
    }

    try:
        await api.create_payment(payment_data)
        word = "расход" if direction_id == 510 else "приход"
        await message.answer(f"✅ {word.capitalize()} успешно добавлен!", reply_markup=main_menu)
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке: {e}", reply_markup=main_menu)
    finally:
        await state.clear()