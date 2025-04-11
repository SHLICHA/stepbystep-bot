from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_categories_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='🏋️ Здоровье', callback_data='category_health'),
            InlineKeyboardButton(text='💼 Карьера', callback_data='category_career')
        ],
        [
            InlineKeyboardButton(text='📚 Обучение', callback_data='category_study'),
            InlineKeyboardButton(text='❤️ Личное', callback_data='category_personal')
        ],
        [
            InlineKeyboardButton(text='◀️ Отмена', callback_data='back_to_main')
        ]
    ])

def get_back_kb(target: str = 'main') -> InlineKeyboardMarkup:
    '''Универсальная клавиатура "Назад"'''
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='\U0001F519 Назад', callback_data=f'back_to_{target}')
        ]
    ])

def get_main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='\U0001F4A1 Добавить цель', callback_data='add_goal')],
        [InlineKeyboardButton(text='\U0001F4DD Мои цели', callback_data='my_goals')]
    ])

def get_deadline_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1 неделя", callback_data="deadline_1_week"),
            InlineKeyboardButton(text="1 месяц", callback_data="deadline_1_month")
        ],
        [
            InlineKeyboardButton(text="3 месяца", callback_data="deadline_3_months"),
            InlineKeyboardButton(text="6 месяцев", callback_data="deadline_6_months")
        ],
        [
            InlineKeyboardButton(text="❌ Без срока", callback_data="deadline_none")
        ]
    ])

def get_goals_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📌 Активные цели", callback_data="goals_active"),
            InlineKeyboardButton(text="✅ Завершенные", callback_data="goals_completed")
        ],
        [
            InlineKeyboardButton(text="📅 По срокам", callback_data="goals_by_deadline"),
            InlineKeyboardButton(text="🗂 По категориям", callback_data="goals_by_category")
        ],
        [
            InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_to_main")
        ]
    ])

def get_goals_pagination_kb(total: int, current_index: int) -> InlineKeyboardMarkup:
    buttons = []
    
    # Кнопки навигации (оставляем как было)
    if total > 1:
        nav_buttons = []
        if current_index > 0:
            nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"goal_prev_{current_index}"))
        
        nav_buttons.append(InlineKeyboardButton(
            text=f"{current_index+1}/{total}", 
            callback_data="current_page"
        ))
        
        if current_index < total - 1:
            nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"goal_next_{current_index}"))
        
        buttons.append(nav_buttons)
    
    # Обновленные кнопки действий
    buttons.extend([
        [
            InlineKeyboardButton(
                text="🏠 В главное меню", 
                callback_data="back_to_main"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Обновить", 
                callback_data="refresh_goals"
            )
        ]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_edit_goal_kb(goal_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для редактирования цели"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Название", callback_data=f"edit_title_{goal_id}"),
            InlineKeyboardButton(text="📅 Срок", callback_data=f"edit_deadline_{goal_id}")
        ],
        [
            InlineKeyboardButton(text="◀️ Назад к цели", callback_data=f"goal_detail_{goal_id}"),
            InlineKeyboardButton(text="🏠 В меню", callback_data="back_to_main")
        ]
    ])

def get_delete_confirm_kb(goal_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_{goal_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"goal_edit_{goal_id}")
        ]
    ])

def get_completed_goals_kb() -> InlineKeyboardMarkup:
    """Дополнительная клавиатура для завершенных целей"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🧹 Очистить историю", callback_data="clear_completed"),
            InlineKeyboardButton(text="◀️ Назад", callback_data="goals_active")
        ]
    ])