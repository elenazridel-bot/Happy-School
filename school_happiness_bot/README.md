# Бот школы «Счастья»

Telegram-бот на [aiogram 3](https://docs.aiogram.dev/), который приветствует
пользователя фразой «Здравствуйте! Я ищу людей, которые счастливы, — чтобы
вместе построить школу «Счастья»», ведёт с ним диалог и собирает контакты
(имя, город, чем готов помочь, телефон), сохраняя их в базу SQLite.

## Диалог бота

1. `/start` — приветствие и вопрос об имени.
2. Город.
3. Выбор способа помощи (кнопки): обучение, организация, волонтёрство,
   финансовая поддержка, другое.
4. Телефон — кнопкой «Отправить номер телефона» или вручную.
5. Подтверждение введённых данных.
6. Сохранение контакта в `contacts.db` и (опционально) уведомление
   администратора в Telegram.

`/cancel` в любой момент прерывает диалог.

## Установка

```bash
cd school_happiness_bot
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Настройка

1. Получите токен бота у [@BotFather](https://t.me/BotFather).
2. Скопируйте `.env.example` в `.env` и заполните:

```bash
cp .env.example .env
```

```
BOT_TOKEN=123456:ваш_токен
ADMIN_CHAT_ID=123456789   # необязательно: ваш chat_id для уведомлений
```

Узнать свой `chat_id` можно, например, у бота [@userinfobot](https://t.me/userinfobot).

## Запуск

```bash
python bot.py
```

Бот сохраняет собранные контакты в файл `contacts.db` (SQLite) в таблице
`contacts`. Просмотреть их можно, например, так:

```bash
sqlite3 contacts.db "SELECT * FROM contacts;"
```

## Структура проекта

```
school_happiness_bot/
├── bot.py           # точка входа, запуск polling
├── config.py        # чтение настроек из .env
├── database.py       # работа с SQLite
├── handlers.py       # логика диалога (FSM)
├── keyboards.py       # inline/reply-клавиатуры
├── states.py         # состояния диалога
├── requirements.txt
├── .env.example
└── README.md
```
