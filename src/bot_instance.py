from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from src.config.settings import settings
from src.middleware.antispam_middleware import AntispamMiddleware

bot = Bot(token=settings.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

dp.middleware.setup(AntispamMiddleware(cooldown_seconds=2))