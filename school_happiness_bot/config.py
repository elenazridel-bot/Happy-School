import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_chat_id: Optional[int]


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "BOT_TOKEN не задан. Добавьте его в файл .env (см. .env.example)."
        )

    admin_id_raw = os.getenv("ADMIN_CHAT_ID")
    admin_id = int(admin_id_raw) if admin_id_raw else None

    return Config(bot_token=token, admin_chat_id=admin_id)
