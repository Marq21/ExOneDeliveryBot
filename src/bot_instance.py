# src/bot_instance.py
import socket
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from src.config.settings import settings
from src.middleware.antispam_middleware import AntispamMiddleware


class TimeoutBot(Bot):
    """
    Bot с оптимизированными таймаутами и поддержкой Happy Eyeballs.
    """

    async def get_session(self) -> aiohttp.ClientSession:
        """Возвращает aiohttp-сессию с оптимизированными параметрами."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(
                total=60,       # общий таймаут запроса
                connect=10,     # уменьшен с 30 до 10 секунд
                sock_connect=5, # НОВОЕ: таймаут именно на установку TCP-соединения
                sock_read=30,   # уменьшен с 60 до 30 секунд
            )
            
            # Коннектор с Happy Eyeballs
            # family=AF_UNSPEC - разрешает и IPv4, и IPv6
            # happy_eyeballs_delay=0.25 - если IPv4 не отвечает 250 мс, пробуем IPv6
            # ttl_dns_cache=300 - кэшируем DNS на 5 минут, чтобы не спамить резолвер
            connector = aiohttp.TCPConnector(
                family=socket.AF_UNSPEC,
                happy_eyeballs_delay=0.25,
                ttl_dns_cache=300,
                limit=100,                  # максимум одновременных соединений
                limit_per_host=20,          # максимум соединений к api.telegram.org
            )
            
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
            )
        return self._session


bot = TimeoutBot(token=settings.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(AntispamMiddleware(cooldown_seconds=0.5))