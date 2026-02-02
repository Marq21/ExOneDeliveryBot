import logging
from dotenv import load_dotenv
from aiogram import executor
from aiogram import types
from src.bot_instance import dp
from src.handlers.start import get_main_menu, register_start_handlers
from src.handlers.send_code import register_send_code_handlers
from src.handlers.global_handlers import register_global_callbacks
from src.handlers.error_handlers import register_error_handlers # <-- Новый импорт

# Логирование в файл
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler() # Также вывод в консоль
    ]
)

async def handle_unknown_message(message: types.Message):
    """Обрабатывает все неизвестные текстовые сообщения."""
    await message.answer(
        "❓ Я вас не понимаю.\n"
        "Пожалуйста, воспользуйтесь кнопками меню для навигации.",
        reply_markup=get_main_menu()
    )

logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Регистрация всех компонентов
register_error_handlers(dp)      # Сначала ошибки
register_global_callbacks(dp)   # Потом глобальные хендлеры
register_send_code_handlers(dp) # Потом специфичные
register_start_handlers(dp)
dp.register_message_handler(handle_unknown_message, content_types=types.ContentTypes.TEXT)


if __name__ == '__main__':
    logger.info("🚀 Бот запущен...")
    executor.start_polling(dp, skip_updates=True)