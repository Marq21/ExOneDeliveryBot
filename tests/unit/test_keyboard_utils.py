import pytest
from aiogram.types import InlineKeyboardButton
from src.utils.keyboard_utils import (
    get_store_selection_keyboard,
    get_ozon_pvz_keyboard,
    get_office_keyboard,
    get_back_to_menu_inline
)
from src.utils.config_loader import ConfigLoader


def test_get_store_selection_keyboard():
    """Тест: клавиатура выбора магазина содержит OZON и WB."""
    kb = get_store_selection_keyboard()
    buttons = [btn.text for row in kb.inline_keyboard for btn in row]

    assert "📦 OZON" in buttons
    assert "📦 Wildberries" in buttons


def test_get_office_keyboard():
    """Тест: клавиатура офисов соответствует конфигу."""
    kb = get_office_keyboard()
    buttons = [btn.text for row in kb.inline_keyboard for btn in row if btn.callback_data.startswith("office_")]

    config = ConfigLoader.get_config()
    expected_offices = {f"📍 {office['name']} ({office['address'].split(',')[0]})" for office in config["offices"]}

    actual_buttons = set(buttons)
    assert actual_buttons == expected_offices


def test_get_ozon_pvz_keyboard():
    """Тест: клавиатура ПВЗ OZON содержит ожидаемые пункты."""
    kb = get_ozon_pvz_keyboard()
    buttons = [btn.text for row in kb.inline_keyboard for btn in row if btn.callback_data.startswith("ozon_pvz_")]

    # Ожидаем, что в dev-конфиге есть два ПВЗ
    expected_pvzs = {"Троллейбусная 24/2В", "50-летия Ростсельмаша 1/52"}
    assert set(buttons) == expected_pvzs


def test_get_back_to_menu_inline():
    """Тест: кнопка 'В меню' ведёт в главное меню."""
    kb = get_back_to_menu_inline()
    button = kb.inline_keyboard[0][0]
    assert button.text == "🏠 В меню"
    assert button.callback_data == "back_to_menu"