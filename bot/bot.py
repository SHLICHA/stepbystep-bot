import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from django.conf import settings

from bot.states import GoalCreation, GoalEditStates
from .handlers import start, goals, add_goal_handler, daedline_handler
from bot.handlers.back_handler import handle_back
from .handlers.categories import handle_category_selection
from .handlers.goals import handle_goal_title
from .handlers.my_goals import *
from .handlers.goal_actions import *


bot = Bot(
    token=settings.TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(bot=bot)

dp.message.register(start.cmd_start, Command('start'))
dp.callback_query.register(handle_category_selection, F.data.startswith('category_'), StateFilter(GoalCreation.waiting_for_category))
dp.callback_query.register(save_goal_with_category, F.data.startswith('confirm_goal'), StateFilter(GoalCreation.waiting_for_deadline))
dp.callback_query.register(handle_back, F.data.in_({'back_to_main', 'back_to_goals_menu'}))
dp.message.register(handle_goal_title, StateFilter(GoalCreation.waiting_for_goal_title))
dp.callback_query.register(add_goal_handler.handle_add_goal, F.data == 'add_goal')
dp.callback_query.register(daedline_handler.handle_deadline, F.data.startswith('deadline_'), StateFilter(GoalCreation.waiting_for_deadline))
#dp.message.register(daedline_handler.handle_custom_deadline, StateFilter('waiting_for_custom_deadline'))
dp.callback_query.register(show_goals_menu, F.data == 'my_goals') # Мои цели
dp.callback_query.register(show_active_goals, F.data == 'goals_active') # Активные цели
dp.callback_query.register(show_goal_detail, F.data.startswith('goal_detail_')) # Информация по цели
dp.callback_query.register(complete_goal, F.data.startswith('goal_complete_')) # Завершенные цели
dp.callback_query.register(delete_goal, F.data.startswith('goal_delete_'))
dp.callback_query.register(confirm_delete_goal, F.data.startswith('confirm_delete_'))
dp.callback_query.register(handle_goal_navigation, F.data.startswith(('goal_prev_', 'goal_next_')))
dp.callback_query.register(refresh_goals_list,F.data == 'refresh_goals') # Обновление списка целей
dp.callback_query.register(show_goals_by_deadline, F.data == 'goals_by_deadline') # По срокам
dp.callback_query.register(show_goals_by_category, F.data == 'goals_by_category') # По категориям
dp.callback_query.register(show_goals_in_category,F.data.startswith('show_category_')) # Показать категорию
dp.callback_query.register(show_completed_goals, F.data == "goals_completed")
dp.callback_query.register(reactivate_goal, F.data.startswith('goal_reactivate_'))
# Редактирование
dp.callback_query.register(start_edit_goal, F.data.startswith('goal_edit_'))
dp.callback_query.register(start_edit_title, F.data.startswith('edit_title_'))
dp.message.register(finish_edit_title, GoalEditStates.editing_title)
dp.callback_query.register(start_edit_deadline, F.data.startswith('edit_deadline_'))
dp.callback_query.register(finish_edit_deadline, F.data.startswith('deadline_'), GoalEditStates.editing_deadline)

dp.callback_query.register(lambda c: c.answer(), F.data == "no_action")