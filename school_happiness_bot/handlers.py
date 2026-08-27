import io
import logging
import re

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from openpyxl import Workbook

from ai import classify_help_type, extract_name
from config import Config
from database import get_all_contacts, save_contact
from keyboards import (
    HELP_TYPES,
    REMOVE_KEYBOARD,
    confirm_keyboard,
    help_type_keyboard,
    phone_request_keyboard,
)
from states import ContactForm

logger = logging.getLogger(__name__)
router = Router()

PHONE_PATTERN = re.compile(r"^\+?\d[\d\s\-()]{6,}$")

GREETING = (
    "Здравствуйте! Я ищу людей, которые счастливы, — чтобы вместе построить "
    "школу «Счастья».\n\n"
    "Я собираю контакты тех, кто готов помочь — обучением, организацией, "
    "волонтёрством или иначе. Это займёт пару минут.\n\n"
    "Как я могу к вам обращаться? Напишите, пожалуйста, ваше имя."
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(GREETING, reply_markup=REMOVE_KEYBOARD)
    await state.set_state(ContactForm.name)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Диалог остановлен. Если захотите начать заново — отправьте /start.",
        reply_markup=REMOVE_KEYBOARD,
    )


@router.message(Command("whoami"))
async def cmd_whoami(message: Message) -> None:
    await message.answer(
        f"Ваш Telegram ID: <code>{message.from_user.id}</code>\n\n"
        "Именно это число должно быть указано в переменной окружения "
        "ADMIN_CHAT_ID, чтобы команда /export была доступна."
    )


@router.message(Command("export"))
async def cmd_export(message: Message, config: Config) -> None:
    user_id = message.from_user.id
    logger.info(
        "Запрос /export от user_id=%s, admin_chat_id из конфига=%s",
        user_id,
        config.admin_chat_id,
    )

    if not config.admin_chat_id:
        await message.answer(
            "ADMIN_CHAT_ID не задан в настройках бота, поэтому /export "
            "недоступен никому. Добавьте переменную окружения ADMIN_CHAT_ID "
            "(узнать свой ID можно командой /whoami)."
        )
        return

    if user_id != config.admin_chat_id:
        await message.answer(
            f"Команда /export доступна только администратору. Ваш ID "
            f"(<code>{user_id}</code>) не совпадает с ADMIN_CHAT_ID в "
            "настройках бота. Проверьте значение командой /whoami."
        )
        return

    try:
        contacts = await get_all_contacts()
        if not contacts:
            await message.answer("Пока нет ни одного сохранённого контакта.")
            return

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Контакты"
        sheet.append(
            ["Имя", "Город", "Готов(а) помочь", "Телефон", "Telegram", "Дата регистрации"]
        )
        for row in contacts:
            username = f"@{row['username']}" if row["username"] else ""
            sheet.append(
                [
                    row["full_name"],
                    row["city"],
                    row["help_type"],
                    row["phone"],
                    username,
                    row["created_at"],
                ]
            )
        for column_cells in sheet.columns:
            max_length = max(len(str(cell.value or "")) for cell in column_cells)
            sheet.column_dimensions[column_cells[0].column_letter].width = max_length + 2

        buffer = io.BytesIO()
        workbook.save(buffer)
        buffer.seek(0)

        await message.answer_document(
            BufferedInputFile(buffer.read(), filename="school_happiness_contacts.xlsx"),
            caption=f"Контактов: {len(contacts)}",
        )
    except Exception:
        logger.exception("Не удалось сформировать/отправить экспорт контактов")
        await message.answer(
            "Не получилось сформировать файл — произошла ошибка. "
            "Подробности есть в логах сервиса."
        )


@router.message(ContactForm.name, F.text)
async def process_name(message: Message, state: FSMContext) -> None:
    raw_text = message.text.strip()
    name = await extract_name(raw_text)
    if len(name) < 2:
        await message.answer("Пожалуйста, введите имя текстом (не короче 2 символов).")
        return

    await state.update_data(name=name)
    await message.answer(f"Приятно познакомиться, {name}! Из какого вы города?")
    await state.set_state(ContactForm.city)


@router.message(ContactForm.name)
async def process_name_invalid(message: Message) -> None:
    await message.answer("Пожалуйста, напишите ваше имя текстом.")


@router.message(ContactForm.city, F.text)
async def process_city(message: Message, state: FSMContext) -> None:
    city = message.text.strip()
    if len(city) < 2:
        await message.answer("Пожалуйста, укажите город текстом.")
        return

    await state.update_data(city=city)
    await message.answer(
        "Чем вы могли бы помочь школе «Счастья»? Выберите подходящий вариант "
        "кнопкой или просто опишите своими словами:",
        reply_markup=help_type_keyboard(),
    )
    await state.set_state(ContactForm.help_type)


@router.message(ContactForm.city)
async def process_city_invalid(message: Message) -> None:
    await message.answer("Пожалуйста, укажите город текстом.")


@router.callback_query(ContactForm.help_type, F.data.startswith("help:"))
async def process_help_type(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":", 1)[1]
    label = HELP_TYPES.get(key, "Другое")

    await state.update_data(help_type=label)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Отлично! Теперь поделитесь номером телефона — нажмите кнопку ниже "
        "или введите номер вручную.",
        reply_markup=phone_request_keyboard(),
    )
    await state.set_state(ContactForm.phone)
    await callback.answer()


@router.message(ContactForm.help_type, F.text)
async def process_help_type_text(message: Message, state: FSMContext) -> None:
    key = await classify_help_type(message.text.strip())
    label = HELP_TYPES[key]

    await state.update_data(help_type=label)
    await message.answer(
        f"Записал: «{label}». Теперь поделитесь номером телефона — нажмите "
        "кнопку ниже или введите номер вручную.",
        reply_markup=phone_request_keyboard(),
    )
    await state.set_state(ContactForm.phone)


@router.message(ContactForm.phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext) -> None:
    phone = message.contact.phone_number
    await finish_phone_step(message, state, phone)


@router.message(ContactForm.phone, F.text)
async def process_phone_text(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()
    if not PHONE_PATTERN.match(phone):
        await message.answer(
            "Похоже, это не похоже на номер телефона. Введите номер в формате "
            "+7XXXXXXXXXX или отправьте его кнопкой ниже.",
            reply_markup=phone_request_keyboard(),
        )
        return

    await finish_phone_step(message, state, phone)


@router.message(ContactForm.phone)
async def process_phone_invalid(message: Message) -> None:
    await message.answer(
        "Пожалуйста, отправьте номер телефона текстом или кнопкой ниже.",
        reply_markup=phone_request_keyboard(),
    )


async def finish_phone_step(message: Message, state: FSMContext, phone: str) -> None:
    await state.update_data(phone=phone)
    data = await state.get_data()

    summary = (
        "Проверьте, пожалуйста, данные:\n\n"
        f"Имя: {data['name']}\n"
        f"Город: {data['city']}\n"
        f"Готов(а) помочь: {data['help_type']}\n"
        f"Телефон: {data['phone']}\n"
    )
    await message.answer(summary, reply_markup=REMOVE_KEYBOARD)
    await message.answer("Всё верно?", reply_markup=confirm_keyboard())
    await state.set_state(ContactForm.confirm)


@router.callback_query(ContactForm.confirm, F.data == "confirm:no")
async def process_confirm_no(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(GREETING)
    await state.set_state(ContactForm.name)
    await callback.answer()


@router.callback_query(ContactForm.confirm, F.data == "confirm:yes")
async def process_confirm_yes(
    callback: CallbackQuery, state: FSMContext, config: Config
) -> None:
    data = await state.get_data()
    user = callback.from_user

    await save_contact(
        telegram_id=user.id,
        username=user.username,
        full_name=data["name"],
        city=data["city"],
        help_type=data["help_type"],
        phone=data["phone"],
    )

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Спасибо! Ваши контакты сохранены. Мы свяжемся с вами, когда будем "
        "формировать команду школы «Счастья». 🙏"
    )
    await state.clear()
    await callback.answer("Контакты сохранены")

    if config.admin_chat_id:
        await notify_admin(callback.bot, config.admin_chat_id, data, user)


async def notify_admin(bot: Bot, admin_chat_id: int, data: dict, user) -> None:
    telegram_line = f"Telegram: @{user.username}" if user.username else "Telegram: не указан"
    notify_text = (
        "Новая заявка в школу «Счастья»:\n\n"
        f"Имя: {data['name']}\n"
        f"Город: {data['city']}\n"
        f"Готов(а) помочь: {data['help_type']}\n"
        f"Телефон: {data['phone']}\n"
        f"{telegram_line}"
    )
    try:
        await bot.send_message(admin_chat_id, notify_text)
    except Exception:
        logger.exception("Не удалось отправить уведомление администратору")
