from aiogram.fsm.state import State, StatesGroup


class FinishStates(StatesGroup):
    waiting_ombor_photo = State()
    waiting_bosh_joy_photo = State()
