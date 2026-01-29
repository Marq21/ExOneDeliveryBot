from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from src.utils.config_loader import ConfigLoader


def get_main_menu() -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру главного меню."""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(KeyboardButton("📤 Отправить код"))
    markup.add(KeyboardButton("❓ Ответы на вопросы"))
    return markup


async def cmd_start(message: types.Message):
    """Обработчик команды /start."""
    await message.answer(
        "Привет! Я бот для работы с кодами выдачи заказов.\n"
        "Выберите действие:",
        reply_markup=get_main_menu()
    )


async def send_faq(message: types.Message):
    """Отправляет ответы на частые вопросы."""
    config = ConfigLoader.get_config()
    lines = ["<b>❓ Ответы на вопросы</b>\n"]

    # График работы
    lines.append("<b>🕐 График работы:</b>")
    for office in config["offices"]:
        office_id = office["id"]
        schedule = config["office_schedules"].get(office_id, "Не указан")
        lines.append(f"• {office['name']}: {schedule}")

    lines.append("\n<b>📍 Адреса пунктов выдачи:</b>")
    for office in config["offices"]:
        lines.append(f"• {office['name']}: {office['address']}")

    lines.append("\n❗ Все коды принимаются только на Троллейбусной 24/2В.")
    await message.answer("\n".join(lines), parse_mode="HTML")


def register_start_handlers(dp: Dispatcher):
    """Регистрация всех хендлеров из этого модуля."""
    dp.register_message_handler(cmd_start, commands=["start"])

    dp.register_message_handler(
        send_faq,
        lambda msg: msg.text == "❓ Ответы на вопросы",
        state="*"
    )