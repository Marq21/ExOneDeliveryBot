# src/bot_instance.py
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from src.config.settings import settings
from src.middleware.antispam_middleware import AntispamMiddleware


class TimeoutBot(Bot):
    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(
                total=120,      
                connect=30,     
                sock_read=60,   
            )
            
            self._session = aiohttp.ClientSession(
                timeout=timeout,
            )
        return self._session


bot = TimeoutBot(token=settings.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(AntispamMiddleware(cooldown_seconds=0.5))