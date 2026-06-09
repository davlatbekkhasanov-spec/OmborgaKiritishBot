"""Bugungi yakunlangan sessiyalar — deploydan keyin hub ga qayta yuborish."""

from __future__ import annotations

import sqlite3

from persist_data import bootstrap_persistence, resolve_db_path

_DB_BOOT = bootstrap_persistence(
    resolve_db_path(env_key="HUB_DAY_LOG_PATH", default_filename="omborga_hub_day.db"),
    legacy_names=("omborga_hub_day.db",),
)
_DB = _DB_BOOT["db_path"]
HUB_DB_PATH = _DB


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(_DB, timeout=15)
    c.row_factory = sqlite3.Row
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS hub_day_push (
            day TEXT NOT NULL,
            tg_id INTEGER NOT NULL,
            summary TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (day, tg_id)
        )
        """
    )
    c.commit()
    return c


def save_today_push(*, day: str, tg_id: int, summary: str) -> None:
    from datetime import datetime

    text = " ".join(str(summary or "").split())[:420]
    if not text or not tg_id:
        return
    with _conn() as c:
        c.execute(
            """
            INSERT INTO hub_day_push(day, tg_id, summary, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(day, tg_id) DO UPDATE SET
                summary = excluded.summary,
                updated_at = excluded.updated_at
            """,
            (day, int(tg_id), text, datetime.now().isoformat(timespec="seconds")),
        )
        c.commit()


def list_today_pushes(day: str) -> list[tuple[int, str]]:
    with _conn() as c:
        cur = c.execute(
            "SELECT tg_id, summary FROM hub_day_push WHERE day = ?",
            (day,),
        )
        return [(int(r["tg_id"]), str(r["summary"])) for r in cur.fetchall()]
