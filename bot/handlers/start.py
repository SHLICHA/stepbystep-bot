from aiogram import types

from bot.keyboards import get_categories_kb, get_main_menu_kb
from core.models import User

async def cmd_start(message: types.Message):
    user, created = await User.objects.aget_or_create(
        telegram_id=message.from_user.id,
        defaults={
            'first_name': message.from_user.first_name,
        }
    )
    await message.answer(
        f'Привет, {user.first_name}! Я помогу тебе в достижении твоих целей \U0001F680',
        reply_markup=get_main_menu_kb()
    )