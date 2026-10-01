# src/bot_instance.py
import socket
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from src.config.settings import settings
from src.middleware.antispam_middleware import AntispamMiddleware


class TimeoutBot(Bot):
    """
    Bot с оптимизированными таймаутами и настройками пула соединений.
    """

    async def get_session(self) -> aiohttp.ClientSession:
        """Возвращает aiohttp-сессию с оптимизированными параметрами."""
        if self._session is None or self._session.closed:
            # Уменьшаем таймауты, чтобы бот не висел по минуте при сетевых проблемах
            timeout = aiohttp.ClientTimeout(
                total=60,        # общий таймаут запроса
                connect=10,      # таймаут на установку соединения (было 30)
                sock_connect=5,  # жёсткий таймаут на TCP-handshake
                sock_read=30,    # таймаут ожидания данных (было 60)
            )
            
            # Настраиваем коннектор
            # family=AF_UNSPEC разрешает и IPv4, и IPv6
            # ttl_dns_cache=300 кэширует DNS на 5 минут
            # enable_cleanup_closed=True предотвращает утечки сокетов
            connector = aiohttp.TCPConnector(
                family=socket.AF_UNSPEC,
                ttl_dns_cache=300,
                limit=100,                  # максимум одновременных соединений
                limit_per_host=20,          # максимум соединений к api.telegram.org
                enable_cleanup_closed=True,
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