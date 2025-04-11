from aiogram import types
from aiogram.fsm.context import FSMContext
from bot.states import GoalCreation
from bot.keyboards import get_categories_kb
import logging

logger = logging.getLogger(__name__)

async def handle_add_goal(callback: types.CallbackQuery, state: FSMContext):
    try:
        await state.set_state(GoalCreation.waiting_for_category)
        await callback.message.edit_text(
            "📂 Сначала выберите категорию для новой цели:",
            reply_markup=get_categories_kb()
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error starting goal creation: {e}")
        await callback.answer("⚠️ Ошибка при создании цели")