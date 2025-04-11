import time

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from goals.models import Goal
from core.models import User
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def save_goal_with_deadline(state: FSMContext, deadline_date: datetime):
    data = await state.get_data()
    user = await User.objects.aget(telegram_id=data['user_id'])
    goal = await Goal.objects.acreate(
        user=user,
        title=data['goal_title'],
        category=data['category'],
        deadline=deadline_date.date()  # Преобразуем datetime в date
    )
    return goal

def calculate_deadline(period: str) -> datetime:
    """Альтернативная версия с точным расчетом месяцев"""
    now = datetime.now()
    period_map = {
        '1_week': now + timedelta(weeks=1),
        '2_weeks': now + timedelta(weeks=2),
        '1_month': now + relativedelta(months=1),
        '3_months': now + relativedelta(months=3),
        '6_months': now + relativedelta(months=6),
        '1_year': now + relativedelta(years=1)
    }
    return period_map.get(period, now + timedelta(weeks=1))

def parse_custom_deadline(text: str) -> datetime:
    """Парсим пользовательский ввод срока"""
    try:
        value, unit = text.split()
        value = int(value)
        
        if 'недел' in unit.lower():
            return datetime.now() + timedelta(weeks=value)
        elif 'месяц' in unit.lower():
            return datetime.now() + timedelta(days=value*30)
        elif 'год' in unit.lower():
            return datetime.now() + timedelta(days=value*365)
    except (ValueError, AttributeError):
        raise ValueError("Неверный формат срока")

async def get_user_goals(telegram_id: int, filters: dict = None):
    """Получение целей с улучшенной фильтрацией"""
    query = Goal.objects.filter(
        user__telegram_id=telegram_id,
        **{k: v for k, v in (filters or {}).items() if v is not None}
    )
    if filters and filters.get('is_completed'):
        query = query.order_by('-completed_at')  # Сначала новые завершенные
    else:
        query = query.order_by('deadline')  # Активные по сроку 
    return [goal async for goal in query]

async def get_goals_by_deadline(telegram_id):
    """Группировка целей по срокам выполнения"""
    now = timezone.now().date()
    
    # Получаем все активные цели пользователя
    goals_query = Goal.objects.filter(
        user__telegram_id=telegram_id,
        is_completed=False,
        deadline__isnull=False
    ).order_by('deadline')
    
    goals = []
    async for goal in goals_query:
        goals.append(goal)
    
    # Группируем цели по срокам
    goals_by_deadline = {
        "Просроченные": [],
        "Сегодня": [],
        "Завтра": [],
        "На этой неделе": [],
        "В этом месяце": [],
        "Позже": []
    }
    
    for goal in goals:
        delta = (goal.deadline - now).days
        
        if delta < 0:
            goals_by_deadline["Просроченные"].append(goal)
        elif delta == 0:
            goals_by_deadline["Сегодня"].append(goal)
        elif delta == 1:
            goals_by_deadline["Завтра"].append(goal)
        elif delta < 7:
            goals_by_deadline["На этой неделе"].append(goal)
        elif delta < 30:
            goals_by_deadline["В этом месяце"].append(goal)
        else:
            goals_by_deadline["Позже"].append(goal)
    
    # Удаляем пустые группы
    return {k: v for k, v in goals_by_deadline.items() if v}

async def get_goals_by_category(telegram_id: int) -> dict:
    """Группировка целей по категориям"""
    goals = {}
    
    all_goals = Goal.objects.filter(
        user__telegram_id=telegram_id,
        is_completed=False
    ).order_by('category', 'deadline')

    async for goal in all_goals:
        if goal.category not in goals:
            goals[goal.category] = []
        goals[goal.category].append(goal)
    
    return goals

def _get_pagination_row(index: int, total: int) -> list:
    """Генерирует ряд пагинации с уникальными callback_data"""
    row = []
    if index > 0:
        row.append(InlineKeyboardButton(
            text="⬅️ Назад", 
            callback_data=f"prev_{index}_{time.time()}"  # Добавляем timestamp для уникальности
        ))
    
    row.append(InlineKeyboardButton(
        text=f"{index+1}/{total}", 
        callback_data=f"page_{index}_{time.time()}"
    ))
    
    if index < total - 1:
        row.append(InlineKeyboardButton(
            text="Вперед ➡️", 
            callback_data=f"next_{index}_{time.time()}"
        ))
    
    return row