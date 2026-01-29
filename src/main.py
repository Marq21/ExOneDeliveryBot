import logging
from dotenv import load_dotenv
from aiogram import executor
from src.bot_instance import dp
from src.exceptions import SpamDetected
from src.handlers.send_code import register_send_code_handlers
from src.handlers.start import register_start_handlers 
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()

register_send_code_handlers(dp)
register_start_handlers(dp)

logger = logging.getLogger(__name__)
logger.debug("[DEBUG] 🚀 Все хендлеры зарегистрированы")


@dp.errors_handler()
async def error_handler(update, exception):
    logger.error(f"Unhandled error: {exception} | Update: {update}")
    if isinstance(exception, SpamDetected):
        return True
    return False


if __name__ == '__main__':
    print("🚀 Бот запущен...")
    executor.start_polling(dp, skip_updates=True)