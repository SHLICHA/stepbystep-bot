import asyncio

from django.core.management.base import BaseCommand

from bot.bot import bot, dp


class Command(BaseCommand):
    help="Запуск Telegram-бота"

    def handle(self, *args, **options):
        async def main():
            await dp.start_polling(bot)
        
        asyncio.run(main())