import asyncio
import logging

import aiohttp
from aiogram import Dispatcher
from aiogram.utils.exceptions import NetworkError

from src.exceptions import SpamDetectedException
from src.utils.admin_notifier import notify_admin_error

logger = logging.getLogger(__name__)


TRANSIENT_NETWORK_EXCEPTIONS = (
    NetworkError,
    aiohttp.ClientError,
    asyncio.TimeoutError,
    ConnectionError,
)


TRANSIENT_MESSAGE_MARKERS = (
    "clientconnectorerror",
    "cannot connect to host",
    "connection reset by peer",
    "server disconnected",
    "connection aborted",
    "timeout",
    "network is unreachable",
    "temporary failure in name resolution",
)


def _is_transient_network_error(exception: Exception) -> bool:
    """
    Проверяет, является ли ошибка временной сетевой ошибкой.

    Такие ошибки обычно не требуют немедленного уведомления администратора,
    если бот в целом продолжает работать.
    """
    if isinstance(exception, TRANSIENT_NETWORK_EXCEPTIONS):
        return True

    exception_text = f"{type(exception).__name__}: {exception}".lower()

    return any(
        marker in exception_text
        for marker in TRANSIENT_MESSAGE_MARKERS
    )


async def error_handler(update, exception):
    """
    Глобальный обработчик всех необработанных исключений.
    """
    await asyncio.sleep(0)

    # Спам/флуд уже обработан middleware, админу не отправляем.
    if isinstance(exception, SpamDetectedException):
        logger.info("Spam attempt was successfully blocked.")
        return True

    # Временные сетевые ошибки только логируем, но не отправляем админу.
    if _is_transient_network_error(exception):
        logger.warning(
            f"Transient network error (admin notification skipped): "
            f"{type(exception).__name__}: {exception}"
        )
        return True

    # Реальные ошибки логируем и отправляем администратору.
    logger.error(
        f"Unhandled error: {exception} | Update: {update}"
    )

    error_msg = (
        f"<b>Тип:</b> {type(exception).__name__}\n"
        f"<b>Сообщение:</b> {str(exception)}\n"
        f"<b>Update ID:</b> {update.update_id if hasattr(update, 'update_id') else 'N/A'}"
    )

    await notify_admin_error(error_msg)

    return False


def register_error_handlers(dp: Dispatcher):
    dp.register_errors_handler(error_handler)