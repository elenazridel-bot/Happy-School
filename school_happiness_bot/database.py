from datetime import datetime, timezone
from typing import Optional

import aiosqlite

DB_PATH = "contacts.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    username TEXT,
    full_name TEXT NOT NULL,
    city TEXT NOT NULL,
    help_type TEXT NOT NULL,
    phone TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_TABLE_SQL)
        await db.commit()


async def save_contact(
    telegram_id: int,
    username: Optional[str],
    full_name: str,
    city: str,
    help_type: str,
    phone: str,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO contacts
                (telegram_id, username, full_name, city, help_type, phone, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                telegram_id,
                username,
                full_name,
                city,
                help_type,
                phone,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        await db.commit()
