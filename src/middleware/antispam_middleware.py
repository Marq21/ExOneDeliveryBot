# src/middleware/antispam_middleware.py
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram import types
import time
import logging

from src.exceptions import SpamDetectedException

logger = logging.getLogger(__name__)

class AntispamMiddleware(BaseMiddleware):
    def __init__(self, cooldown_seconds: int = 2):
        super().__init__()
        self.cooldown = cooldown_seconds
        # Используем отдельные словари для сообщений и callback'ов
        self.last_message_time = {}
        self.last_callback_time = {}

    async def on_pre_process_message(self, message: types.Message,  dict):
        user_id = message.from_user.id
        now = time.time()
        last_time = self.last_message_time.get(user_id, 0)
        
        if now - last_time < self.cooldown:
            logger.warning(f"⚠️ Spam detected (message) from user {user_id}")
            await message.answer("⏳ Не так быстро! Подождите немного.")
            raise SpamDetectedException("Spam blocked")
        else:
            self.last_message_time[user_id] = now

    async def on_pre_process_callback_query(self, callback: types.CallbackQuery,  dict):
        user_id = callback.from_user.id
        now = time.time()
        last_time = self.last_callback_time.get(user_id, 0)
        
        if now - last_time < self.cooldown:
            logger.warning(f"⚠️ Spam detected (callback) from user {user_id}")
            await callback.answer("⏳ Не так быстро!", show_alert=True)
            raise SpamDetectedException("Spam blocked")
        else:
            self.last_callback_time[user_id] = now