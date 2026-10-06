"""
Aiogram Bot and Dispatcher initialization.
Uses MemoryStorage for FSMContext as requested.
"""

import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from django.conf import settings

# Explicit MemoryStorage for FSMContext
storage = MemoryStorage()

# Retrieve token from Django settings or environment
BOT_TOKEN = getattr(
    settings,
    'TELEGRAM_BOT_TOKEN',
    os.getenv('TELEGRAM_BOT_TOKEN', '123456789:ABCDefGhIJklMNopQRstUVwxyz')
)

try:
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
except (ImportError, TypeError, AttributeError):
    bot = Bot(token=BOT_TOKEN)

# Dispatcher with MemoryStorage for FSM state handling
dp = Dispatcher(storage=storage)
