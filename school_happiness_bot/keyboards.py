from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

HELP_TYPES = {
    "teaching": "Обучение и наставничество",
    "organizing": "Организация мероприятий",
    "volunteering": "Волонтёрство",
    "funding": "Финансовая поддержка",
    "other": "Другое",
}


def help_type_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"help:{key}")]
        for key, label in HELP_TYPES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def phone_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Всё верно", callback_data="confirm:yes"),
                InlineKeyboardButton(text="✏️ Начать заново", callback_data="confirm:no"),
            ]
        ]
    )


REMOVE_KEYBOARD = ReplyKeyboardRemove()
