"""
Утилиты для генерации клавиатур (InlineKeyboardMarkup).
Вынесены из хендлеров для улучшения читаемости и тестируемости.
"""
import aiogram.types
from pathlib import Path
from src.utils.config_loader import ConfigLoader


def get_main_menu() -> aiogram.types.ReplyKeyboardMarkup:
    """Возвращает клавиатуру главного меню."""
    markup = aiogram.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=False)
    markup.add(aiogram.types.KeyboardButton("📤 Отправить код"))
    markup.add(aiogram.types.KeyboardButton(
        "🔄 Перезапустить бота"))
    # markup.add(aiogram.types.KeyboardButton("❓ Ответы на вопросы"))
    return markup


def get_store_selection_keyboard() -> aiogram.types.InlineKeyboardMarkup:
    """
    Клавиатура выбора маркетплейса на этапе CHOOSING_STORE.
    """
    markup = aiogram.types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        aiogram.types.InlineKeyboardButton(
            "📦 OZON", callback_data="store_ozon"),
        aiogram.types.InlineKeyboardButton(
            "📦 Wildberries", callback_data="store_wildberries")
    )
    return markup


# def get_ozon_pvz_keyboard() -> aiogram.types.InlineKeyboardMarkup:
#     """
#     Клавиатура выбора пункта выдачи OZON (ПВЗ).
#     Использует данные из конфига: ozon_pvzs.
#     """
#     keyboard = aiogram.types.InlineKeyboardMarkup(row_width=1)
#     config = ConfigLoader.get_config()
#     pvzs = config.get("ozon_pvzs", [])

#     if not pvzs:
#         # Fallback на случай, если в конфиге нет ПВЗ
#         keyboard.add(aiogram.types.InlineKeyboardButton(
#             "Троллейбусная 24/2В", callback_data="ozon_pvz_trolleibusnaya"))
#         keyboard.add(aiogram.types.InlineKeyboardButton(
#             "ул. 50-летия Ростсельмаша 1/52", callback_data="ozon_pvz_rostselmash"))
#     else:
#         for pvz in pvzs:
#             keyboard.add(
#                 aiogram.types.InlineKeyboardButton(
#                     text=pvz["name"],
#                     callback_data=f"ozon_pvz_{pvz['id']}"
#                 )
#             )

    keyboard.row(
        aiogram.types.InlineKeyboardButton(
            "◀️ Назад", callback_data="back_to_store_choice"),
        aiogram.types.InlineKeyboardButton(
            "🏠 В меню", callback_data="back_to_menu")
    )
    return keyboard


def get_office_keyboard() -> aiogram.types.InlineKeyboardMarkup:
    """
    Клавиатура выбора офиса получения заказа.
    Использует данные из конфига: offices.
    """
    keyboard = aiogram.types.InlineKeyboardMarkup(row_width=1)
    config = ConfigLoader.get_config()
    for office in config.get("offices", []):
        # Извлекаем часть адреса до первой запятой для краткости
        full_address = office['address']
        short_address = full_address.split(
            ',')[0] if ',' in full_address else full_address
        button_text = f"📍 {office['name']} ({short_address})"
        keyboard.add(
            aiogram.types.InlineKeyboardButton(
                text=button_text,
                callback_data=f"office_{office['id']}"
            )
        )
    keyboard.row(
        aiogram.types.InlineKeyboardButton(
            "◀️ Назад", callback_data="back_to_store_choice"),
        aiogram.types.InlineKeyboardButton(
            "🏠 В меню", callback_data="back_to_menu")
    )
    return keyboard


def get_back_to_menu_inline() -> aiogram.types.InlineKeyboardMarkup:
    """
    Простая клавиатура с одной кнопкой "В меню".
    """
    return aiogram.types.InlineKeyboardMarkup().add(
        aiogram.types.InlineKeyboardButton(
            "🏠 В меню", callback_data="back_to_menu")
    )
