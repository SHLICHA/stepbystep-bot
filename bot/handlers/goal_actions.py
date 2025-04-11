import datetime

from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from django.utils import timezone

from core.models import User
from goals.models import Goal
from bot.services import calculate_deadline, get_user_goals
from bot.keyboards import (
    get_main_menu_kb,
    get_goals_menu_kb,
    get_edit_goal_kb,
    get_deadline_kb,
    get_delete_confirm_kb  # Добавим эту функцию
)
from bot.handlers.my_goals import show_active_goals, show_completed_goals, format_date


class GoalEditStates(StatesGroup):
    editing_title = State()
    editing_deadline = State()
    editing_category = State()

async def _verify_goal_owner(telegram_id: int, goal_id: int) -> Goal:
    """Проверяет владельца цели и возвращает объект"""
    try:
        goal = await Goal.objects.select_related('user').aget(
            id=goal_id,
            user__telegram_id=telegram_id
        )
        return goal
    except Goal.DoesNotExist:
        raise TelegramBadRequest("Цель не найдена или нет доступа")
    
async def save_goal_with_category(callback: types.CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        
        # Преобразуем строку даты обратно в datetime
        deadline_str = data.get('deadline')
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date() if deadline_str else None
        
        goal = await Goal.objects.acreate(
            user=await User.objects.aget(telegram_id=callback.from_user.id),
            title=data['title'],
            category=data['category'],
            deadline=deadline,  # Может быть None
            is_completed=False
        )
        await callback.message.answer(
            f"✅ Цель создана!\nСрок: {goal.deadline.strftime('%d.%m.%Y') if goal.deadline else 'не указан'}",
            reply_markup=get_main_menu_kb()
        )
        await state.clear()
        
    except Exception as e:
        await callback.answer("⚠️ Ошибка при создании цели")
        await state.clear()

async def complete_goal(callback: types.CallbackQuery, state: FSMContext):
    """Отметка цели как выполненной"""
    goal_id = int(callback.data.split('_')[-1])
    goal = await _verify_goal_owner(callback.from_user.id, goal_id)
    
    await Goal.objects.filter(id=goal_id).aupdate(
        is_completed=True,
        completed_at=timezone.now()  # Автоматически проставится в save()
    )
    
    await callback.answer("✅ Цель выполнена!")
    await show_active_goals(callback, state)

async def delete_goal(callback: types.CallbackQuery, state: FSMContext):
    """Удаление цели с учетом текущего раздела"""
    try:
        goal_id = int(callback.data.split('_')[-1])
        goal = await _verify_goal_owner(callback.from_user.id, goal_id)
        
        # Получаем текущий тип целей из состояния
        data = await state.get_data()
        goals_type = data.get('goals_type', 'active')
        
        await Goal.objects.filter(id=goal_id).adelete()
        await callback.answer("🗑 Цель удалена!")
        
        # Возвращаем в соответствующий раздел
        if goals_type == 'completed':
            await show_completed_goals(callback, state)
        else:
            await show_active_goals(callback, state)
            
    except Exception as e:
        await callback.answer("⚠️ Ошибка при удалении цели")

async def confirm_delete_goal(callback: types.CallbackQuery, state: FSMContext):
    """Подтверждение удаления с учетом раздела"""
    try:
        goal_id = int(callback.data.split('_')[-1])
        goal = await _verify_goal_owner(callback.from_user.id, goal_id)
        
        # Получаем тип целей из состояния
        data = await state.get_data()
        goals_type = data.get('goals_type', 'active')
        
        # Создаем клавиатуру с возвратом в нужный раздел
        back_target = "goals_completed" if goals_type == 'completed' else "goals_active"
        
        await callback.message.edit_text(
            f"❌ Вы уверены, что хотите удалить цель?\n\n"
            f"<b>{goal.title}</b>\n"
            f"Категория: {goal.category}\n"
            f"Срок: {format_date(goal.deadline, 'нет срока')}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_{goal_id}"),
                    InlineKeyboardButton(text="❌ Отмена", callback_data=back_target)
                ]
            ]),
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        await callback.answer("⚠️ Ошибка при подтверждении удаления")

async def start_edit_goal(callback: types.CallbackQuery, state: FSMContext):
    """Меню редактирования цели (основной обработчик)"""
    goal_id = int(callback.data.split('_')[-1])
    goal = await _verify_goal_owner(callback.from_user.id, goal_id)
    
    await state.update_data(edit_goal_id=goal_id)
    
    await callback.message.edit_text(
        f"✏️ <b>Редактирование цели:</b>\n\n"
        f"<b>Название:</b> {goal.title}\n"
        f"<b>Категория:</b> {goal.category}\n"
        f"<b>Срок:</b> {goal.deadline.strftime('%d.%m.%Y') if goal.deadline else 'нет срока'}\n\n"
        f"Выберите что изменить:",
        reply_markup=get_edit_goal_kb(goal_id),
        parse_mode="HTML"
    )
    await callback.answer()

async def start_edit_title(callback: types.CallbackQuery, state: FSMContext):
    """Начало редактирования названия"""
    goal_id = int(callback.data.split('_')[-1])
    await _verify_goal_owner(callback.from_user.id, goal_id)
    
    await state.set_state(GoalEditStates.editing_title)
    await state.update_data(edit_goal_id=goal_id)
    
    await callback.message.edit_text(
        "✏️ Введите новое название цели:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Отмена", callback_data=f"goal_edit_{goal_id}")]
        ])
    )
    await callback.answer()

async def finish_edit_title(message: types.Message, state: FSMContext):
    """Финальный обработчик изменения названия"""
    # Проверяем, что мы именно в состоянии редактирования
    if await state.get_state() != GoalEditStates.editing_title:
        return
    
    data = await state.get_data()
    goal_id = data['edit_goal_id']
    
    # Валидация длины названия
    if len(message.text) < 3:
        await message.answer("❌ Слишком короткое название (минимум 3 символа)")
        return
    if len(message.text) > 100:
        await message.answer("❌ Слишком длинное название (максимум 100 символов)")
        return
    
    # Обновляем цель в базе
    await Goal.objects.filter(id=goal_id).aupdate(title=message.text)
    
    # Получаем обновленные данные
    goal = await Goal.objects.aget(id=goal_id)
    
    # 1. Удаляем сообщение с полем ввода
    try:
        await message.bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id - 1
        )
    except:
        pass
    
    # 2. Показываем обновленную информацию
    await message.answer(
        f"✅ Название обновлено!\n\n"
        f"<b>{goal.title}</b>\n"
        f"Категория: {goal.category}\n"
        f"Срок: {goal.deadline.strftime('%d.%m.%Y') if goal.deadline else 'нет срока'}",
        reply_markup=get_edit_goal_kb(goal_id),
        parse_mode="HTML"
    )
    
    # 3. Полностью очищаем состояние
    await state.clear()

async def start_edit_deadline(callback: types.CallbackQuery, state: FSMContext):
    """Начало редактирования срока"""
    goal_id = int(callback.data.split('_')[-1])
    await _verify_goal_owner(callback.from_user.id, goal_id)
    
    await state.set_state(GoalEditStates.editing_deadline)
    await state.update_data(edit_goal_id=goal_id)
    
    await callback.message.edit_text(
        "📅 Выберите новый срок:",
        reply_markup=get_deadline_kb()
    )
    await callback.answer()

async def finish_edit_deadline(callback: types.CallbackQuery, state: FSMContext):
    """Сохранение нового срока"""
    data = await state.get_data()
    goal_id = data['edit_goal_id']
    
    if callback.data.startswith('deadline_'):
        period = callback.data.split('_')[1]
        deadline_date = calculate_deadline(period)
        await Goal.objects.filter(id=goal_id).aupdate(deadline=deadline_date.date())
        await state.clear()
        
        goal = await Goal.objects.aget(id=goal_id)
        await callback.message.edit_text(
            f"✅ Срок обновлен!\n\n"
            f"<b>{goal.title}</b>\n"
            f"Категория: {goal.category}\n"
            f"Новый срок: {goal.deadline.strftime('%d.%m.%Y')}",
            reply_markup=get_edit_goal_kb(goal_id),
            parse_mode="HTML"
        )
    await callback.answer()

async def reactivate_goal(callback: types.CallbackQuery, state: FSMContext):
    """Возвращаем цель в активные"""
    goal_id = int(callback.data.split('_')[-1])
    goal = await _verify_goal_owner(callback.from_user.id, goal_id)
    
    await Goal.objects.filter(id=goal_id).aupdate(
        is_completed=False,
        completed_at=None
    )
    await callback.answer("🔙 Цель возвращена в активные!")
    await show_completed_goals(callback, state)