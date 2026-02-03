import logging
from aiogram import Bot
from src.utils.config_loader import ConfigLoader
from src.bot_instance import bot

logger = logging.getLogger(__name__)

async def notify_admin_error(message: str):
    """
    Отправляет сообщение об ошибке в админский чат.
    """
    try:
        config = ConfigLoader.get_config()
        chat_id = config.get("admin_error_chat_id")
        if not chat_id:
            logger.warning("Admin error chat ID not configured. Skipping notification.")
            return

        # Ограничиваем длину сообщения (Telegram limit ~4096)
        if len(message) > 4000:
            message = message[:3997] + "..."

        await bot.send_message(
            chat_id=chat_id,
            text=f"🚨 <b>CRITICAL ERROR</b>\n\n{message}",
            parse_mode="HTML"
        )
        logger.info("Admin error notification sent successfully.")
    except Exception as e:
        logger.error(f"Failed to send admin error notification: {e}")