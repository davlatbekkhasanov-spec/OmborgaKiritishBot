from aiogram.fsm.state import State, StatesGroup


class StartStates(StatesGroup):
    waiting_start_photo = State()


class FinishStates(StatesGroup):
    waiting_ombor_photo = State()
    waiting_bosh_joy_photo = State()
