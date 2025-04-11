import logging

from time import timezone
from aiogram import types, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from django.db.models import Q
import logging

from bot.keyboards import get_goals_menu_kb, get_edit_goal_kb, get_delete_confirm_kb
from bot.services import get_user_goals, get_goals_by_category, get_goals_by_deadline
from goals.models import Goal

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('goals.log')
    ]
)
logger = logging.getLogger(__name__)

def format_date(date_obj, default_text="не указано"):
    return date_obj.strftime('%d.%m.%Y %H:%M') if date_obj else default_text

def _get_pagination_buttons(current_index: int, total: int) -> list[list[InlineKeyboardButton]]:
    """Генерация кнопок пагинации с логированием"""
    logger.info(f"Генерация кнопок пагинации. Текущая: {current_index}, Всего: {total}")
    
    buttons = []
    if total > 1:
        row = []
        if current_index > 0:
            prev_btn = InlineKeyboardButton(
                text="⬅️ Назад", 
                callback_data=f"goal_prev_{current_index}"
            )
            row.append(prev_btn)
            logger.info(f"Добавлена кнопка 'Назад': {prev_btn.callback_data}")
        
        counter_btn = InlineKeyboardButton(
            text=f"{current_index+1}/{total}", 
            callback_data="no_action"
        )
        row.append(counter_btn)
        
        if current_index < total - 1:
            next_btn = InlineKeyboardButton(
                text="Вперед ➡️", 
                callback_data=f"goal_next_{current_index}"
            )
            row.append(next_btn)
            logger.info(f"Добавлена кнопка 'Вперед': {next_btn.callback_data}")
        
        buttons.append(row)
    
    logger.info(f"Сгенерированы кнопки: {buttons}")
    return buttons

async def show_goals_menu(callback: types.CallbackQuery):
    """Показываем меню 'Мои цели'"""
    try:
        await callback.message.edit_text(
            "\U0001F4CB <b>Мои цели</b>\nВыберите тип отображения:",
            reply_markup=get_goals_menu_kb()
        )
    except TelegramBadRequest as e:
        logger.warning(f"Message not modified: {e}")
    except Exception as e:
        logger.error(f"Error showing goals menu: {e}")
        await callback.message.answer("⚠️ Произошла ошибка при загрузке меню")
    finally:
        await callback.answer()

async def show_active_goals(callback: types.CallbackQuery, state: FSMContext):
    """Показ активных целей с логированием"""
    try:
        logger.info("Загрузка активных целей...")
        goals = await get_user_goals(
            telegram_id=callback.from_user.id,
            filters={'is_completed': False}
        )
        
        logger.info(f"Найдено активных целей: {len(goals)}")
        
        if not goals:
            logger.warning("У пользователя нет активных целей")
            await callback.message.edit_text(
                "🛑 У вас нет активных целей!",
                reply_markup=get_goals_menu_kb()
            )
            return
            
        logger.info("Сохранение целей в состоянии...")
        await state.update_data(
            goals=goals,
            current_index=0,
            goals_type='active'
        )
        
        logger.info("Отображение первой цели...")
        await _display_goal_page(callback, goals[0], 0, len(goals))
        
    except Exception as e:
        logger.error(f"Ошибка при показе активных целей: {e}")
        await callback.message.answer(
            "⚠️ Ошибка при загрузке целей",
            reply_markup=get_goals_menu_kb()
        )
    finally:
        await callback.answer()

async def _display_goal_page(callback: types.CallbackQuery, goal: Goal, index: int, total: int):
    """Универсальный вывод цели с кнопкой удаления"""
    text = (
        f"📌 <b>Цель {index+1}/{total}</b>\n\n"
        f"<b>{goal.title}</b>\n"
        f"Категория: {goal.category}\n"
        f"Срок: {format_date(goal.deadline, 'нет срока')}"
    )
    
    builder = InlineKeyboardBuilder()
    
    # Основные кнопки действий
    if goal.is_completed:
        builder.row(
            InlineKeyboardButton(text="↩️ Вернуть в работу", callback_data=f"goal_reactivate_{goal.id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"goal_delete_{goal.id}"),
            width=2
        )
    else:
        builder.row(
            InlineKeyboardButton(text="✅ Выполнена", callback_data=f"goal_complete_{goal.id}"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"goal_edit_{goal.id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"goal_delete_{goal.id}"),
            width=2
        )
    
    # Кнопки пагинации
    if total > 1:
        pagination_buttons = []
        if index > 0:
            pagination_buttons.append(InlineKeyboardButton(
                text="⬅️ Назад", 
                callback_data=f"goal_prev_{index}"
            ))
        
        pagination_buttons.append(InlineKeyboardButton(
            text=f"{index+1}/{total}", 
            callback_data="no_action"
        ))
        
        if index < total - 1:
            pagination_buttons.append(InlineKeyboardButton(
                text="Вперед ➡️", 
                callback_data=f"goal_next_{index}"
            ))
        
        builder.row(*pagination_buttons)
    
    # Кнопка возврата (разные для активных и завершенных)
    back_button = InlineKeyboardButton(
        text="◀️ Назад к списку", 
        callback_data="goals_completed" if goal.is_completed else "goals_active"
    )
    builder.row(back_button)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

async def handle_goal_navigation(callback: types.CallbackQuery, state: FSMContext):
    """Обработка переключения между целями с полным логированием"""
    try:
        logger.info(f"Получен callback: {callback.data}")
        
        data = await state.get_data()
        goals = data.get('goals', [])
        logger.info(f"Найдено целей в состоянии: {len(goals)}")
        
        if not goals:
            logger.error("В состоянии нет целей!")
            await callback.answer("Нет целей для отображения")
            return
            
        current_index = data.get('current_index', 0)
        logger.info(f"Текущий индекс: {current_index}")
        
        # Безопасный парсинг callback_data
        try:
            _, action, index_str = callback.data.split('_')
            index = int(index_str)
            logger.info(f"Обработка действия: {action}, индекс: {index}")
        except Exception as e:
            logger.error(f"Ошибка парсинга callback_data: {e}")
            await callback.answer("Ошибка обработки команды")
            return

        # Вычисляем новый индекс
        new_index = current_index
        if action == 'next':
            new_index = min(index + 1, len(goals) - 1)
            logger.info(f"Кнопка 'Вперед'. Новый индекс: {new_index}")
        elif action == 'prev':
            new_index = max(index - 1, 0)
            logger.info(f"Кнопка 'Назад'. Новый индекс: {new_index}")
        
        if new_index == current_index:
            logger.info("Индекс не изменился")
            await callback.answer()
            return
            
        logger.info(f"Обновление индекса с {current_index} на {new_index}")
        await state.update_data(current_index=new_index)
        
        # Получаем цель
        goal = goals[new_index]
        logger.info(f"Отображаем цель: ID={goal.id}, '{goal.title}'")
        
        # Формируем сообщение
        text = (
            f"📌 <b>Цель {new_index+1}/{len(goals)}</b>\n\n"
            f"<b>{goal.title}</b>\n"
            f"Категория: {goal.category}\n"
            f"Срок: {goal.deadline.strftime('%d.%m.%Y') if goal.deadline else 'нет срока'}"
        )
        
        # Создаем клавиатуру
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Выполнена", 
                    callback_data=f"complete_{goal.id}"
                ),
                InlineKeyboardButton(
                    text="✏️ Редактировать", 
                    callback_data=f"edit_{goal.id}"
                )
            ],
            *_get_pagination_buttons(new_index, len(goals)),
            [
                InlineKeyboardButton(
                    text="◀️ Назад в меню", 
                    callback_data="back_to_goals_menu"
                )
            ]
        ])
        
        try:
            await callback.message.edit_text(
                text,
                reply_markup=kb,
                parse_mode="HTML"
            )
            logger.info("Сообщение успешно обновлено")
        except TelegramBadRequest as e:
            logger.error(f"Ошибка Telegram при редактировании: {e}")
            await callback.answer("Обновите список целей")
        
    except Exception as e:
        logger.error(f"Критическая ошибка в навигации: {e}", exc_info=True)
        await callback.answer("⚠️ Ошибка при переключении")

async def show_completed_goals(callback: types.CallbackQuery, state: FSMContext):
    """Показываем список завершенных целей"""
    try:
        goals = await get_user_goals(
            telegram_id=callback.from_user.id,
            filters={'is_completed': True}
        )
        
        if not goals:
            await callback.message.edit_text(
                "🎉 У вас пока нет завершенных целей!",
                reply_markup=get_goals_menu_kb()
            )
            return
            
        await state.update_data(
            goals=goals,
            current_index=0,
            goals_type='completed'
        )
        
        await _display_goal_page(callback, goals[0], 0, len(goals))
        
    except Exception as e:
        logger.error(f"Error showing completed goals: {e}")
        await callback.message.answer(
            "⚠️ Произошла ошибка при загрузке завершенных целей",
            reply_markup=get_goals_menu_kb()
        )
    finally:
        await callback.answer()

async def show_goals_by_deadline(callback: types.CallbackQuery):
    """Показ целей, сгруппированных по срокам"""
    try:
        goals_by_deadline = await get_goals_by_deadline(callback.from_user.id)
        
        if not goals_by_deadline:
            await callback.message.edit_text(
                "Нет активных целей для отображения по срокам",
                reply_markup=get_goals_menu_kb()
            )
            return
        
        text = "📅 <b>Цели по срокам:</b>\n\n"
        for group, goals in goals_by_deadline.items():
            text += f"<b>{group}:</b>\n"
            text += "\n".join(
                f"• {goal.title} ({goal.deadline.strftime('%d.%m.%Y') if goal.deadline else 'без срока'})" 
                for goal in goals
            )
            text += "\n\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_goals_menu_kb(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error showing goals by deadline: {e}")
        await callback.message.answer("⚠️ Ошибка при загрузке целей по срокам")
    finally:
        await callback.answer()

async def show_goals_by_category(callback: types.CallbackQuery):
    """Показ целей, сгруппированных по категориям"""
    try:
        goals_by_category = await get_goals_by_category(callback.from_user.id)
        
        if not goals_by_category:
            await callback.message.edit_text(
                "Нет активных целей для отображения по категориям",
                reply_markup=get_goals_menu_kb()
            )
            return
        
        # Строим клавиатуру с категориями
        builder = InlineKeyboardBuilder()
        for category in goals_by_category.keys():
            builder.button(
                text=f"{category} ({len(goals_by_category[category])})",
                callback_data=f"show_category_{category}"
            )
        builder.button(text="◀️ Назад", callback_data="back_to_goals_menu")
        builder.adjust(1)  # По одной кнопке в строке
        
        await callback.message.edit_text(
            "📂 <b>Выберите категорию:</b>",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error showing goals by category: {e}")
        await callback.message.answer("⚠️ Ошибка при загрузке целей по категориям")
    finally:
        await callback.answer()

async def show_goals_in_category(callback: types.CallbackQuery):
    """Показ целей конкретной категории"""
    try:
        category = callback.data.split('_')[-1]
        
        goals_query = Goal.objects.filter(
            user__telegram_id=callback.from_user.id,
            category=category,
            is_completed=False
        ).order_by('deadline')

        goals = []
        async for goal in goals_query:
            goals.append({
                'title': goal.title,
                'deadline': goal.deadline
            })
        
        text = f"📂 <b>Категория: {category}</b>\n\n"
        text += "\n".join(
            f"• {goal['title']} ({goal['deadline'].strftime('%d.%m.%Y') if goal['deadline'] else 'без срока'})"
            for goal in goals
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_goals_menu_kb(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error showing goals in category: {e}")
        await callback.message.answer("⚠️ Ошибка при загрузке целей категории")
    finally:
        await callback.answer()

async def show_goal_detail(callback: types.CallbackQuery):
    """Просмотр конкретной цели"""
    try:
        goal_id = int(callback.data.split('_')[-1])
        goal = await Goal.objects.aget(id=goal_id)
        
        await callback.message.edit_text(
            f"📌 <b>{goal.title}</b>\n\n"
            f"Категория: {goal.category}\n"
            f"Срок: {format_date(goal.deadline, 'нет срока')}\n"
            f"Статус: {'✅ Выполнена' if goal.is_completed else '🟡 В процессе'}\n"
            f"Создана: {format_date(goal.created_at)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"goal_edit_{goal.id}"),
                    InlineKeyboardButton(text="✅ Выполнена", callback_data=f"goal_complete_{goal.id}")
                ],
                [
                    InlineKeyboardButton(text="🗑 Удалить", callback_data=f"goal_delete_{goal.id}"),
                    InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_goals_menu")
                ]
            ]),
            parse_mode="HTML"
        )
    except Goal.DoesNotExist:
        await callback.answer("Цель не найдена")
    except Exception as e:
        logger.error(f"Error showing goal detail: {e}")
        await callback.answer("⚠️ Ошибка при загрузке цели")
    finally:
        await callback.answer()

async def refresh_goals_list(callback: types.CallbackQuery, state: FSMContext):
    """Обновление списка целей"""
    try:
        await callback.answer("🔄 Обновляю список...")
        
        # Получаем текущий тип целей из состояния
        data = await state.get_data()
        goals_type = data.get('goals_type', 'active')
        
        # В зависимости от типа вызываем соответствующую функцию
        if goals_type == 'completed':
            await show_completed_goals(callback, state)
        else:
            await show_active_goals(callback, state)
            
    except Exception as e:
        logger.error(f"Error refreshing goals list: {e}")
        await callback.answer("⚠️ Ошибка при обновлении")