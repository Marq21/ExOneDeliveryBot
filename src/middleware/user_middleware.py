from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram import types

class UserMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: types.Message, data: dict):
        # Заглушка: ничего не делаем
        pass

    async def on_pre_process_callback_query(self, callback_query: types.CallbackQuery, data: dict):
        # Заглушка: ничего не делаем
        pass