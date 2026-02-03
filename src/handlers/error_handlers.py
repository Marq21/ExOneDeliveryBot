import asyncio
import logging
from aiogram import Dispatcher
from src.exceptions import SpamDetectedException
from src.utils.admin_notifier import notify_admin_error

logger = logging.getLogger(__name__)

async def error_handler(update, exception):
    """
    Глобальный обработчик всех необработанных исключений.
    """
    await asyncio.sleep(0)
    logger.error(f"Unhandled error: {exception} | Update: {update}")
    
    if isinstance(exception, SpamDetectedException):
        logger.info("Spam attempt was successfully blocked.")
        return True  # Ошибка обработана, не отправляем в админ-чат
    
    # Отправляем уведомление админу только для реальных ошибок
    error_msg = (
        f"🚨 <b>CRITICAL ERROR</b>\n"
        f"<b>Тип:</b> {type(exception).__name__}\n"
        f"<b>Сообщение:</b> {str(exception)}\n"
        f"<b>Update ID:</b> {update.update_id if hasattr(update, 'update_id') else 'N/A'}"
    )
    await notify_admin_error(error_msg)
    
    return False  # Aiogram может показать traceback (если нужно)

def register_error_handlers(dp: Dispatcher):
    dp.register_errors_handler(error_handler)