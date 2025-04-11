from aiogram import F, types
from aiogram.fsm.context import FSMContext
from bot.states import GoalCreation
from bot.keyboards import get_deadline_kb
import logging

logger = logging.getLogger(__name__)

async def handle_goal_title(message: types.Message, state: FSMContext):
    try:
        if len(message.text) < 3:
            await message.answer("❌ Название слишком короткое (мин. 3 символа)")
            return
            
        await state.update_data(title=message.text)
        await state.set_state(GoalCreation.waiting_for_deadline)
        
        await message.answer(
            "📅 Теперь выберите срок выполнения:",
            reply_markup=get_deadline_kb()
        )
    except Exception as e:
        logger.error(f"Error in handle_goal_title: {e}")
        await message.answer("⚠️ Ошибка при обработке названия")
