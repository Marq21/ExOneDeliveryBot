# src/main.py
import asyncio
import logging
from dotenv import load_dotenv
from aiogram import types
from src.bot_instance import dp, bot
from src.handlers.start import get_main_menu, register_start_handlers
from src.handlers.send_code import register_send_code_handlers
from src.handlers.global_handlers import register_global_callbacks
from src.handlers.error_handlers import register_error_handlers

# Логирование в файл
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

POLLING_RESTART_DELAY = 10  # секунд между перезапусками


async def handle_unknown_message(message: types.Message):
    """Обрабатывает все неизвестные текстовые сообщения."""
    await message.answer(
        "❓ Я вас не понимаю.\n"
        "Пожалуйста, воспользуйтесь кнопками меню для навигации.",
        reply_markup=get_main_menu()
    )


async def heartbeat():
    """Периодический heartbeat для мониторинга живости бота."""
    while True:
        logger.info("HEARTBEAT: Bot is alive")
        await asyncio.sleep(300)  # Каждые 5 минут


async def resilient_polling():
    """
    Запуск polling с автоматическим перезапуском при сбоях.
    """
    while True:
        try:
            logger.info("🔄 Запуск polling...")
            # reset_webhook=False — не пытаемся удалить вебхук (это вызывает таймаут)
            await dp.start_polling(bot, reset_webhook=False)
        except KeyboardInterrupt:
            logger.info("⛔ Получен сигнал остановки (KeyboardInterrupt).")
            break
        except Exception as e:
            logger.exception(
                f"💥 Polling crashed: {type(e).__name__}: {e}. "
                f"Перезапуск через {POLLING_RESTART_DELAY} сек..."
            )
            await asyncio.sleep(POLLING_RESTART_DELAY)


# Загрузка переменных окружения
load_dotenv()

# Регистрация всех компонентов
register_error_handlers(dp)
register_global_callbacks(dp)
register_start_handlers(dp)
register_send_code_handlers(dp)
dp.register_message_handler(handle_unknown_message, content_types=types.ContentTypes.TEXT)


if __name__ == '__main__':
    logger.info("🚀 Бот запущен...")

    # Запускаем ВСЁ в одном event loop — это критично!
    # Раньше executor.start_polling сам создавал loop, теперь мы управляем им явно.
    loop = asyncio.get_event_loop()
    
    # Параллельные задачи: heartbeat + resilient polling
    tasks = [
        loop.create_task(heartbeat()),
        loop.create_task(resilient_polling()),
    ]
    
    try:
        loop.run_until_complete(asyncio.gather(*tasks))
    except KeyboardInterrupt:
        logger.info("⛔ Бот остановлен пользователем.")
    finally:
        # Корректное закрытие aiohttp-сессии (добавим в bot_instance.py ниже)
        loop.run_until_complete(bot.close())
        logger.info("👋 Бот завершил работу.")