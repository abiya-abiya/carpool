"""
Entrypoint for running the aiogram Telegram bot directly.
"""

import asyncio
import logging
import os
import sys

# Ensure Django environment is configured
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carpool.settings')

try:
    import django
    django.setup()
except Exception as e:
    logging.error(f"Error setting up Django: {e}")

from rides.bot.bot_instance import bot, dp
from rides.bot.handlers import setup_routers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Initializing Carpool Telegram Bot...")
    # Register routers
    dp.include_router(setup_routers())

    logger.info("Starting bot polling with MemoryStorage FSM...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user.")
