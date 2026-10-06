"""
Django management command to run the aiogram Telegram bot.
Usage: python manage.py runbot
"""

import asyncio
import logging
from django.core.management.base import BaseCommand
from rides.bot.bot_instance import bot, dp
from rides.bot.handlers import setup_routers

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Runs the Carpool aiogram Telegram bot with MemoryStorage FSM."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting Carpool Telegram Bot..."))

        async def run():
            dp.include_router(setup_routers())
            self.stdout.write(self.style.SUCCESS("Handlers and FSM routers registered successfully."))
            self.stdout.write(self.style.SUCCESS("Listening for Telegram updates..."))
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot)

        try:
            asyncio.run(run())
        except (KeyboardInterrupt, SystemExit):
            self.stdout.write(self.style.WARNING("Bot stopped."))
