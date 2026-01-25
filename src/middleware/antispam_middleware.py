# src/middleware/antispam_middleware.py
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram import types
from collections import defaultdict
import time

class AntispamMiddleware(BaseMiddleware):
    def __init__(self, cooldown_seconds: int = 2):
        super().__init__()
        self.cooldown = cooldown_seconds
        self.user_last_message = defaultdict(float)

    async def on_pre_process_message(self, message: types.Message, data: dict):
        user_id = message.from_user.id
        now = time.time()

        if now - self.user_last_message[user_id] < self.cooldown:
            await message.answer("⏳ Пожалуйста, не отправляйте сообщения слишком часто.")
            raise Exception("Spam detected")

        self.user_last_message[user_id] = now