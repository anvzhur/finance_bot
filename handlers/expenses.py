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
from handlers.start import get_main_menu
from database import get_user_info, log_simple_operation
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

@router.message(F.text == "➕ Добавить расход")
async def add_expense_start(message: Message, state: FSMContext):
    user_info = await get_user_info(message.from_user.id)
    if not user_info or not user_info.get("api_key"):
        await message.answer("❌ Вы не зарегистрированы. Обратитесь к администратору.")
        return
    await state.update_data(
        operation_type="expense",
        direction_id=510,
        api_key=user_info["api_key"]
    )
    await _start_operation_flow(message, state)

@router.message(F.text == "➕ Добавить приход")
async def add_income_start(message: Message, state: FSMContext):
    user_info = await get_user_info(message.from_user.id)
    if not user_info or not user_info.get("api_key"):
        await message.answer("❌ Вы не зарегистрированы. Обратитесь к администратору.")
        return
    await state.update_data(
        operation_type="income",
        direction_id=500,
        api_key=user_info["api_key"]
    )
    await _start_operation_flow(message, state)

async def _proceed_to_organisation(message: Message, state: FSMContext):
    data = await state.get_data()
    api_key = data.get("api_key")
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
        project_map = {"Без проекта": None}
        projects_with_placeholder = [{"projectName": "Без проекта", "id": None}]
        if projects:
            project_map.update({p["projectName"]: p["id"] for p in projects})
            projects_with_placeholder.extend(projects)
        await state.update_data(
            projects=project_map,
            projects_full=projects_with_placeholder
        )
        if not projects:
            await state.update_data(project_id=None, project_name="Без проекта")
            await _proceed_to_organisation(message, state)
        else:
            await message.answer("Выберите проект:", reply_markup=get_project_keyboard(projects_with_placeholder))
            await state.set_state(OperationForm.choosing_project)
    except Exception as e:
        await message.answer(f"❌ Ошибка загрузки проектов: {e}")
        await state.clear()

@router.message(OperationForm.choosing_project)
async def process_project_choice(message: Message, state: FSMContext):
    user_data = await state.get_data()
    project_name = message.text
    project_id = user_data["projects"].get(project_name)
    if project_id is None and project_name != "Без проекта":
        await message.answer("Неверный выбор. Выберите проект из списка.")
        return
    await state.update_data(project_id=project_id, project_name=project_name)
    await _proceed_to_organisation(message, state)

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
        all_accounts = await api.fetch_all_accounts()
        # Фильтруем только счета, принадлежащие выбранной организации
        filtered_accounts = [
            acc for acc in all_accounts
            if acc.get("organisationId") == organisation_id
        ]
        if not filtered_accounts:
            await message.answer("У выбранной организации нет доступных счетов.")
            await state.clear()
            return

        account_map = {
            f"{a['accountName']} ({a['number'][-4:]})": a["id"]
            for a in filtered_accounts
        }
        await state.update_data(accounts=account_map, accounts_full=filtered_accounts)
        await message.answer("Выберите счёт:", reply_markup=get_account_keyboard(filtered_accounts))
        await state.set_state(OperationForm.choosing_account)
    except Exception as e:
        await message.answer(f"❌ Ошибка загрузки счетов: {e}")
        await state.clear()

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

@router.message(OperationForm.confirming)
async def confirm_operation(message: Message, state: FSMContext):
    if message.text not in ("✅ Да", "❌ Нет"):
        await message.answer("Пожалуйста, используйте кнопки для подтверждения.")
        return

    if message.text == "❌ Нет":
        await state.clear()
        await message.answer("Операция отменена.", reply_markup=get_main_menu())
        return

    data = await state.get_data()
    user_info = await get_user_info(message.from_user.id)
    if not user_info or not user_info.get("api_key"):
        await message.answer("❌ Ошибка: API-ключ не найден.", reply_markup=get_main_menu())
        await state.clear()
        return

    api = ReportFinanceAPI(api_key=user_info["api_key"])
    direction_id = data["direction_id"]
    operation_date = datetime.date.today()

    payment_data = {
        "externalId": str(uuid.uuid4()),
        "accountId": data["account_id"],
        "organisationId": data["organisation_id"],
        "paymentDate": operation_date.isoformat(),
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
    if data.get("project_id") is not None:
        payment_data["projectId"] = data["project_id"]

    try:
        await api.create_payment(payment_data)
        await log_simple_operation(
            telegram_id=message.from_user.id,
            operation_type="expense" if direction_id == 510 else "income",
            operation_date=operation_date
        )
        word = "расход" if direction_id == 510 else "приход"
        await message.answer(f"✅ {word.capitalize()} успешно добавлен!", reply_markup=get_main_menu())
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке: {e}", reply_markup=get_main_menu())
    finally:
        await state.clear()