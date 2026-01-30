import asyncio
import logging
from aiogram import Dispatcher
from src.exceptions import SpamDetectedException

logger = logging.getLogger(__name__)

async def error_handler(update, exception):
    """
    Глобальный обработчик всех необработанных исключений.
    """
    await asyncio.sleep(0)
    logger.error(f"Unhandled error: {exception} | Update: {update}")
    
    if isinstance(exception, SpamDetectedException):
        logger.info("Spam attempt was successfully blocked.")
        return True # Говорим aiogram, что ошибка обработана
    
    return False

def register_error_handlers(dp: Dispatcher):
    dp.register_errors_handler(error_handler)