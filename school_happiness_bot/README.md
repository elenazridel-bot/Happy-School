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

## Деплой на Railway

Код бота лежит в подпапке `school_happiness_bot/`, а не в корне репозитория,
поэтому для сборки используются файлы в корне (`railway.json`, `Procfile`,
`requirements.txt`), которые указывают Railway запускать
`python school_happiness_bot/bot.py`. Менять Root Directory сервиса в
настройках Railway не нужно — деплой запускается из корня репозитория.

Что нужно сделать:

1. Создать сервис в Railway и подключить этот репозиторий.
2. В настройках сервиса добавить переменные окружения `BOT_TOKEN` (и, при
   необходимости, `ADMIN_CHAT_ID`) — так же, как в `.env`.
3. Задеплоить. Railway соберёт зависимости из корневого `requirements.txt`
   (он лишь подключает `school_happiness_bot/requirements.txt`) и запустит
   `python school_happiness_bot/bot.py` как процесс `worker` — бот работает
   через polling, отдельный веб-порт ему не нужен.

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
