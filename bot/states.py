from aiogram.fsm.state import StatesGroup, State

from aiogram.fsm.state import StatesGroup, State

class GoalCreation(StatesGroup):
    waiting_for_category = State()
    waiting_for_goal_title = State()
    waiting_for_deadline = State()

class GoalEditStates(StatesGroup):
    editing_title = State()
    editing_deadline = State()
    editing_category = State()