import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional, Sequence

import aiosqlite

DB_PATH = os.getenv("DB_PATH") or "contacts.db"

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


async def get_all_contacts() -> list[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT full_name, city, help_type, phone, username, created_at
            FROM contacts
            ORDER BY id
            """
        ) as cursor:
            return await cursor.fetchall()


def _normalize_phone(phone: Optional[str]) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 11 and digits[0] == "8":
        digits = "7" + digits[1:]
    return digits


def _normalize_telegram(username: Optional[str]) -> str:
    return (username or "").strip().lower()


def deduplicate_contacts(rows: Sequence[aiosqlite.Row]) -> list[aiosqlite.Row]:
    """Убирает повторные заявки одного человека: совпадение по телефону
    (без учёта форматирования и разницы "8"/"+7") или по Telegram-нику
    (без учёта регистра) считается одним и тем же контактом. Из каждой
    группы дублей остаётся самая ранняя заявка — rows должны быть
    отсортированы по времени регистрации, как их отдаёт get_all_contacts."""
    n = len(rows)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a: int, b: int) -> None:
        root_a, root_b = find(a), find(b)
        if root_a != root_b:
            parent[max(root_a, root_b)] = min(root_a, root_b)

    phone_groups: dict[str, list[int]] = defaultdict(list)
    telegram_groups: dict[str, list[int]] = defaultdict(list)
    for i, row in enumerate(rows):
        phone = _normalize_phone(row["phone"])
        telegram = _normalize_telegram(row["username"])
        if phone:
            phone_groups[phone].append(i)
        if telegram:
            telegram_groups[telegram].append(i)

    for groups in (phone_groups, telegram_groups):
        for indices in groups.values():
            for i in indices[1:]:
                union(indices[0], i)

    seen_roots: set[int] = set()
    deduplicated: list[aiosqlite.Row] = []
    for i, row in enumerate(rows):
        root = find(i)
        if root in seen_roots:
            continue
        seen_roots.add(root)
        deduplicated.append(row)

    return deduplicated
