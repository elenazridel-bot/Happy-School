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

    admin_id_raw = (os.getenv("ADMIN_CHAT_ID") or "").strip().strip("'\"")
    if admin_id_raw:
        try:
            admin_id = int(admin_id_raw)
        except ValueError as exc:
            raise RuntimeError(
                f"ADMIN_CHAT_ID={admin_id_raw!r} — не похоже на число. "
                "Укажите числовой Telegram ID (узнать свой можно, отправив "
                "боту команду /whoami, либо через @userinfobot)."
            ) from exc
    else:
        admin_id = None

    return Config(bot_token=token, admin_chat_id=admin_id)
