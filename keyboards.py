# keyboards.py
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from typing import List, Dict, Any

def get_project_keyboard(projects: List[Dict[str, str]]) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for p in projects:
        builder.button(text=p["projectName"])
    builder.adjust(2)
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите проект"
    )

def get_account_keyboard(accounts: List[Dict[str, Any]]) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for a in accounts:
        name = a.get("accountName", "Без названия")
        number = a.get("number", "")
        display = f"{name} ({number[-4:]})" if number else name
        builder.button(text=display)
    builder.adjust(2)
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder=""
    )

def get_confirmation_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="✅ Да")
    builder.button(text="❌ Нет")
    builder.adjust(2)
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Подтвердите операцию"
    )
def get_organisation_keyboard(organisations: List[Dict[str, Any]]) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for org in organisations:
        name = org.get("organisationName") or org.get("name") or f"Организация {org['id']}"
        builder.button(text=name)
    builder.adjust(2)
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите организацию"
    )