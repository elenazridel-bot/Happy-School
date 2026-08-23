from aiogram.fsm.state import State, StatesGroup


class ContactForm(StatesGroup):
    name = State()
    city = State()
    help_type = State()
    phone = State()
    confirm = State()
