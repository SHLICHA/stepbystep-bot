from aiogram import types
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from goals.models import Goal
from core.models import User
from bot.states import GoalCreation
from bot.keyboards import get_main_menu_kb
import logging

logger = logging.getLogger(__name__)

async def handle_deadline(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Получаем данные из callback
        _, period = callback.data.split('_', 1)  # Разделяем только по первому подчеркиванию
        
        if period == 'none':
            # Обработка варианта без срока
            await _save_goal_with_deadline(callback, state, deadline=None)
        else:
            # Обработка вариантов со сроком
            deadline = _calculate_deadline(period)
            await _save_goal_with_deadline(callback, state, deadline)
            
    except Exception as e:
        logger.error(f"Ошибка выбора срока: {e}")
        await callback.answer("⚠️ Ошибка при обработке выбора срока")

def _calculate_deadline(period: str) -> datetime:
    """Вычисляем дату дедлайна на основе периода"""
    today = datetime.now()
    periods = {
        '1_week': timedelta(weeks=1),
        '2_weeks': timedelta(weeks=2),
        '1_month': timedelta(days=30),
        '3_months': timedelta(days=90),
        '6_months': timedelta(days=180),
        '1_year': timedelta(days=365)
    }
    return today + periods.get(period, timedelta(days=1))

async def _save_goal_with_deadline(callback: types.CallbackQuery, state: FSMContext, deadline: datetime | None):
    """Сохраняет цель с указанным сроком (или без него)"""
    try:
        data = await state.get_data()
        
        # Создаем цель
        goal = await Goal.objects.acreate(
            user=await User.objects.aget(telegram_id=callback.from_user.id),
            title=data['title'],
            category=data['category'],
            deadline=deadline.date() if deadline else None,
            is_completed=False
        )
        
        # Формируем текст ответа
        deadline_text = goal.deadline.strftime('%d.%m.%Y') if goal.deadline else "без срока"
        
        await callback.message.answer(
            f"✅ Цель создана!\n\n"
            f"Название: {goal.title}\n"
            f"Категория: {goal.category}\n"
            f"Срок: {deadline_text}",
            reply_markup=get_main_menu_kb()
        )
        
    except Exception as e:
        logger.error(f"Ошибка сохранения цели: {e}")
        await callback.answer("⚠️ Ошибка при создании цели")
    finally:
        await state.clear()