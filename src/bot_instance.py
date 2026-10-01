import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from src.config.settings import settings
from src.middleware.antispam_middleware import AntispamMiddleware


class TimeoutBot(Bot):
    """
    Bot с кастомными таймаутами aiohttp-сессии.
    В aiogram 2.x нельзя передать session в конструктор,
    поэтому переопределяем get_session().
    """

    async def get_session(self) -> aiohttp.ClientSession:
        """Возвращает (или создаёт) aiohttp-сессию с разумными таймаутами."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(
                total=60,       # общий таймаут запроса
                connect=10,     # таймаут установки TCP-соединения
                sock_read=30,   # таймаут ожидания данных от сервера
            )
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session


bot = TimeoutBot(token=settings.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(AntispamMiddleware(cooldown_seconds=0.5))