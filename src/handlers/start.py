from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from src.utils.keyboard_utils import get_main_menu
import logging

logger = logging.getLogger(__name__)

async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start — полный перезапуск."""
    user_id = message.from_user.id
    
    # Проверяем и сбрасываем активное состояние FSM
    current_state = await state.get_state()
    if current_state:
        logger.info(f"🔄 /start command reset FSM state '{current_state}' for user {user_id}")
        await state.finish()
    else:
        logger.debug(f"📍 /start command called by user {user_id} (no active state)")
    
    # Отправляем приветственное сообщение с главным меню
    await message.answer(
        "👋 Привет! Я бот для работы с кодами выдачи заказов.\n"
        "Выберите действие:",
        reply_markup=get_main_menu()
    )

# async def send_faq(message: types.Message):
#     """Отправляет ответы на частые вопросы."""
#     config = ConfigLoader.get_config()
#     lines = ["<b>❓ Ответы на вопросы</b>\n"]

#     # График работы
#     lines.append("<b>🕐 График работы:</b>")
#     for office in config["offices"]:
#         office_id = office["id"]
#         schedule = config["office_schedules"].get(office_id, "Не указан")
#         lines.append(f"• {office['name']}: {schedule}")

#     lines.append("\n<b>📍 Адреса пунктов выдачи:</b>")
#     for office in config["offices"]:
#         lines.append(f"• {office['name']}: {office['address']}")

#     lines.append("\n❗ Все коды принимаются только на Троллейбусной 24/2В.")
#     await message.answer("\n".join(lines), parse_mode="HTML")


def register_start_handlers(dp: Dispatcher):
    """Регистрация всех хендлеров из этого модуля."""
    dp.register_message_handler(
        cmd_start,
        commands=["start"],
        state="*"
    )

    dp.register_message_handler(
        cmd_start,
        lambda msg: msg.text == "🔄 Перезапустить бота",
        state="*"
    )

    # dp.register_message_handler(
    #     send_faq,
    #     lambda msg: msg.text == "❓ Ответы на вопросы",
    #     state="*"
    # )
