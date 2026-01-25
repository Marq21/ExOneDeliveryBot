import asyncio
import logging
from aiogram import executor
from src.bot_instance import dp
from src.handlers.start import register_start_handlers 

# Настройка логгирования
logging.basicConfig(level=logging.INFO)

# Регистрация всех хендлеров
register_start_handlers(dp)

if __name__ == '__main__':
    print("🚀 Бот запущен...")
    executor.start_polling(dp, skip_updates=False)