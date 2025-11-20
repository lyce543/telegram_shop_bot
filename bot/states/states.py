from aiogram.fsm.state import State, StatesGroup


class AddCardStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_photo = State()


class EditCardStates(StatesGroup):
    waiting_for_field_choice = State()
    waiting_for_new_value = State()


class WithdrawalStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_requisites = State()