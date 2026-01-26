import asyncio
import logging
from dotenv import load_dotenv
from aiogram import executor
from src.bot_instance import dp
from src.handlers.start import register_start_handlers 
from src.handlers.send_code import register_send_code_handlers
import logging

logging.basicConfig(level=logging.DEBUG)

load_dotenv()

# Регистрация всех хендлеров
register_send_code_handlers(dp)
register_start_handlers(dp)


if __name__ == '__main__':
    print("🚀 Бот запущен...")
    executor.start_polling(dp, skip_updates=True)