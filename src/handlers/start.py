from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from src.utils.config_loader import ConfigLoader

# Клавиатура главного меню
def get_main_menu() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(KeyboardButton("📤 Отправить код"))
    markup.add(KeyboardButton("🔍 Проверить статус"))
    markup.add(KeyboardButton("❓ Ответы на вопросы"))
    return markup

# Обработчик /start
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот для работы с кодами выдачи заказов.\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu()
    )

# Обработчик текстовых сообщений меню
async def handle_menu(message: types.Message):
    text = message.text.strip()
    if text == "🔍 Проверить статус":
        await message.answer("Функция проверки статуса будет здесь.")
    elif text == "❓ Ответы на вопросы":
        await send_faq(message)
    else:
        # Игнорируем "Отправить код" — его ловит send_code.py
        # Но можно показать меню, если сообщение неизвестное
        if text not in ["📤 Отправить код"]:
            await message.answer("Пожалуйста, используйте кнопки меню.", reply_markup=get_main_menu())

# Отправка FAQ
async def send_faq(message: types.Message):
    config = ConfigLoader.get_config()
    
    # Формируем ответ из office_schedules и offices
    lines = ["<b> Ответы на вопросы</b>\n"]
    
    # График работы
    lines.append("<b> График работы:</b>")
    for office in config["offices"]:
        office_id = office["id"]
        schedule = config["office_schedules"].get(office_id, "Не указан")
        lines.append(f"• {office['name']}: {schedule}")
    
    lines.append("\n<b>? Адреса пунктов выдачи:</b>")
    for office in config["offices"]:
        lines.append(f"• {office['name']}: {office['address']}")
    
    lines.append("\n❗ Все коды принимаются только на Троллейбусной 24/2В.")
    
    await message.answer("\n".join(lines), parse_mode="HTML")

def register_start_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["start"])
    dp.register_message_handler(handle_menu)