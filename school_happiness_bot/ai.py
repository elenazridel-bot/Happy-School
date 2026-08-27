import logging
import os
import re
from typing import Optional

from openai import AsyncOpenAI

from keyboards import HELP_TYPES

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL") or "openai/gpt-4o-mini"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

DEFAULT_HELP_TYPE_KEY = "other"
CLASSIFY_TEMPERATURE = 0.2
EXTRACT_NAME_TEMPERATURE = 0.2

# На случай опечаток вроде "3вут"/"3овут" (цифра вместо "з") при работе без ИИ.
_NAME_PATTERN = re.compile(r"(?:меня\s+)?[з3]ов[ауе]?т\s*[:\-]?\s*(.+)", re.IGNORECASE)

_client: Optional[AsyncOpenAI] = None


def _get_client() -> Optional[AsyncOpenAI]:
    global _client
    if not OPENROUTER_API_KEY:
        return None
    if _client is None:
        _client = AsyncOpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)
    return _client


def _fallback_extract_name(text: str) -> str:
    match = _NAME_PATTERN.search(text)
    if match:
        candidate = match.group(1).strip(" .!,:;-")
        if candidate:
            return candidate
    return text.strip()


async def classify_help_type(text: str) -> str:
    """Определяет категорию из HELP_TYPES по свободному тексту. Новых категорий не придумывает."""
    client = _get_client()
    if client is None:
        return DEFAULT_HELP_TYPE_KEY

    options = "\n".join(f"- {key}: {label}" for key, label in HELP_TYPES.items())
    system_prompt = (
        "Ты классифицируешь сообщение посетителя школы «Счастья» — чем он "
        "готов помочь. Выбери РОВНО ОДИН вариант из списка ниже и ответь "
        "только его ключом на латинице, одним словом, без пояснений и "
        "знаков препинания. Никогда не придумывай категории, которых нет "
        f"в списке. Если не уверен или ничего не подходит — ответь \"{DEFAULT_HELP_TYPE_KEY}\".\n\n"
        f"{options}"
    )

    try:
        response = await client.chat.completions.create(
            model=OPENROUTER_MODEL,
            temperature=CLASSIFY_TEMPERATURE,
            max_tokens=10,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
        )
        raw_key = (response.choices[0].message.content or "").strip().strip("\"'. ").lower()
    except Exception:
        logger.exception("Не удалось классифицировать обращение через OpenRouter")
        return DEFAULT_HELP_TYPE_KEY

    return raw_key if raw_key in HELP_TYPES else DEFAULT_HELP_TYPE_KEY


async def extract_name(text: str) -> str:
    """Достаёт имя из свободного текста ('Меня зовут Владимир' -> 'Владимир')."""
    client = _get_client()
    if client is None:
        return _fallback_extract_name(text)

    system_prompt = (
        "Пользователь Telegram-бота отвечает на вопрос «Как вас зовут?». Он "
        "мог написать просто имя или целую фразу вроде «меня зовут Иван» — "
        "возможно, с опечатками. Верни ТОЛЬКО имя (и фамилию, если она тоже "
        "названа), без вводных слов, кавычек и знаков препинания. Если "
        "явного имени в сообщении нет, верни исходный текст без изменений."
    )

    try:
        response = await client.chat.completions.create(
            model=OPENROUTER_MODEL,
            temperature=EXTRACT_NAME_TEMPERATURE,
            max_tokens=20,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
        )
        extracted = (response.choices[0].message.content or "").strip().strip("\"'")
    except Exception:
        logger.exception("Не удалось извлечь имя через OpenRouter")
        return _fallback_extract_name(text)

    return extracted or _fallback_extract_name(text)
