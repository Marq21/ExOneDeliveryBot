import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from src.config.settings import settings
from src.middleware.antispam_middleware import AntispamMiddleware


class TimeoutBot(Bot):
    """
    Bot с кастомными таймаутами aiohttp-сессии.
    """

    async def get_session(self) -> aiohttp.ClientSession:
        """Возвращает (или создаёт) aiohttp-сессию с разумными таймаутами."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(
                total=120,      # увеличен с 60
                connect=30,     # увеличен с 10
                sock_read=60,   # увеличен с 30
            )
            # family=socket.AF_INET — принудительно использовать IPv4
            # Это обходит проблему, если IPv6 работает, а IPv4 нет
            connector = aiohttp.TCPConnector(family=2)  # AF_INET = 2
            
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
            )
        return self._session


bot = TimeoutBot(token=settings.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(AntispamMiddleware(cooldown_seconds=0.5))