"""Bugungi yakunlangan sessiyalar — deploydan keyin hub ga qayta yuborish."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

_DB = os.getenv("HUB_DAY_LOG_PATH", "/data/omborga_hub_day.db").strip() or "omborga_hub_day.db"


def _conn() -> sqlite3.Connection:
    path = Path(_DB)
    path.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(path), timeout=15)
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
