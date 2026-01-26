from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram import types
import time
from src.exceptions import SpamDetected
import logging

logger = logging.getLogger(__name__)

class AntispamMiddleware(BaseMiddleware):
    def __init__(self, cooldown_seconds: int = 2):
        super().__init__()
        self.cooldown = cooldown_seconds
        self.user_last_action = {}

    async def on_pre_process_message(self, message: types.Message,  data: dict):
        await self._check_spam(message.from_user.id, message)

    async def on_pre_process_callback_query(self, callback: types.CallbackQuery,  data: dict):
        await self._check_spam(callback.from_user.id, callback)

    async def _check_spam(self, user_id: int, obj):
        now = time.time()
        last_time = self.user_last_action.get(user_id, 0)
        logger.debug(f"🛡️ Spam check for user {user_id}, last action: {last_time}, cooldown: {self.cooldown}")

        if now - last_time < self.cooldown:
            logger.warning(f"⚠️ Spam detected from user {user_id}")
            if isinstance(obj, types.Message):
                await obj.answer("⏳ Не так быстро! Подождите немного.")
            elif isinstance(obj, types.CallbackQuery):
                await obj.answer("⏳ Не так быстро!", show_alert=True)
            raise SpamDetected()
        else:
            logger.debug(f"✅ Action allowed for user {user_id}")

        self.user_last_action[user_id] = now