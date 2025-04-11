from aiogram import types, F
from aiogram.fsm.context import FSMContext
from bot.states import GoalCreation
import logging

logger = logging.getLogger(__name__)

async def handle_category_selection(callback: types.CallbackQuery, state: FSMContext):
    try:
        category = callback.data.split('_')[1]
        await state.update_data(category=category)
        await state.set_state(GoalCreation.waiting_for_goal_title)
        
        await callback.message.edit_text(
            f"✏️ Теперь введите название цели для категории '{category}':\n\n"
            f"(Отправьте текстовое сообщение с названием)"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Category selection error: {e}")
        await callback.answer("⚠️ Ошибка выбора категории")