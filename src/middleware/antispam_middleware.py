# src/middleware/antispam_middleware.py
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram import types
import time
import logging

from src.exceptions import SpamDetectedException

logger = logging.getLogger(__name__)


class AntispamMiddleware(BaseMiddleware):
    """
    Анти-спам middleware с защитой от утечки памяти.
    
    - Хранит время последнего сообщения/callback для каждого user_id
    - Периодически чистит устаревшие записи (раз в CLEANUP_INTERVAL)
    - Отдельные кулдауны для сообщений и callback'ов
    """

    # Параметры очистки памяти
    CLEANUP_INTERVAL = 3600   # Проверять раз в 1 час
    MAX_ENTRY_AGE = 600       # Удалять записи старше 10 минут

    def __init__(self, cooldown_seconds: float = 0.5):
        super().__init__()
        self.cooldown = cooldown_seconds
        # Отдельные словари для сообщений и callback'ов
        self.last_message_time: dict[int, float] = {}
        self.last_callback_time: dict[int, float] = {}
        self._last_cleanup: float = time.time()

    def _cleanup_stale_entries(self) -> None:
        """
        Удаляет устаревшие записи из словарей.
        Вызывается не чаще, чем раз в CLEANUP_INTERVAL.
        """
        now = time.time()
        if now - self._last_cleanup < self.CLEANUP_INTERVAL:
            return  # Ещё рано

        stale_msg = [uid for uid, ts in self.last_message_time.items() 
                     if now - ts > self.MAX_ENTRY_AGE]
        stale_cb = [uid for uid, ts in self.last_callback_time.items() 
                    if now - ts > self.MAX_ENTRY_AGE]

        for uid in stale_msg:
            del self.last_message_time[uid]
        for uid in stale_cb:
            del self.last_callback_time[uid]

        if stale_msg or stale_cb:
            logger.debug(
                f"🧹 Cleanup: удалено {len(stale_msg)} записей сообщений, "
                f"{len(stale_cb)} записей callback'ов"
            )

        self._last_cleanup = now

    async def on_pre_process_message(self, message: types.Message, data: dict) -> None:
        """Проверяет спам для обычных сообщений."""
        self._cleanup_stale_entries()

        user_id = message.from_user.id
        now = time.time()
        last_time = self.last_message_time.get(user_id, 0)

        if now - last_time < self.cooldown:
            logger.warning(f"⚠️ Spam detected (message) from user {user_id}")
            await message.answer("⏳ Не так быстро! Подождите немного.")
            raise SpamDetectedException("Spam blocked")
        
        self.last_message_time[user_id] = now

    async def on_pre_process_callback_query(self, callback: types.CallbackQuery, data: dict) -> None:
        """Проверяет спам для callback-запросов (нажатия кнопок)."""
        self._cleanup_stale_entries()

        user_id = callback.from_user.id
        now = time.time()
        last_time = self.last_callback_time.get(user_id, 0)

        if now - last_time < self.cooldown:
            logger.warning(f"⚠️ Spam detected (callback) from user {user_id}")
            await callback.answer("⏳ Не так быстро!", show_alert=True)
            raise SpamDetectedException("Spam blocked")
        
        self.last_callback_time[user_id] = now