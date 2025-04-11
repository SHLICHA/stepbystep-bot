from aiogram import types
from aiogram.fsm.context import FSMContext
from bot.keyboards import get_main_menu_kb, get_goals_menu_kb
import logging

logger = logging.getLogger(__name__)

async def handle_back(callback: types.CallbackQuery, state: FSMContext):
    try:
        logger.info(f"Processing back button with data: {callback.data}")
        
        if callback.data == 'back_to_main':
            await callback.message.edit_text(
                "Главное меню:",
                reply_markup=get_main_menu_kb()
            )
        elif callback.data == 'back_to_goals_menu':
            from bot.handlers.my_goals import show_goals_menu
            await show_goals_menu(callback)
        else:
            logger.warning(f"Unknown back target: {callback.data}")
            await callback.answer()
            
    except Exception as e:
        logger.error(f"Error in back handler: {e}")
        await callback.answer("⚠️ Ошибка при обработке кнопки Назад")