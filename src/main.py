import logging
from dotenv import load_dotenv
from aiogram import executor
from src.bot_instance import dp
from src.handlers.start import register_start_handlers
from src.handlers.send_code import register_send_code_handlers
from src.handlers.global_handlers import register_global_callbacks
from src.handlers.error_handlers import register_error_handlers

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Регистрация всех компонентов
register_error_handlers(dp)      # Сначала ошибки
register_global_callbacks(dp)   # Потом глобальные хендлеры
register_send_code_handlers(dp) # Потом специфичные
register_start_handlers(dp)

if __name__ == '__main__':
    logger.info("🚀 Бот запущен...")
    executor.start_polling(dp, skip_updates=True)