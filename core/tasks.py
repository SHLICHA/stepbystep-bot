from celery import shared_task
from aiogram import Bot
from django.conf import settings
from datetime import date, timedelta

from goals.models import Goal


@shared_task
def check_deadlines():
    """Проверяем приближающиеся дедлайны"""
    tomorrow = date.today() + timedelta(days=1)
    goals = Goal.objects.filter(
        deadline=tomorrow,
        is_completed=False
    )
    
    bot = Bot(token=settings.TELEGRAM_TOKEN)
    for goal in goals:
        bot.send_message(
            chat_id=goal.user.telegram_id,
            text=f"⏰ Напоминание! Завтра дедлайн по цели: {goal.title}"
        )