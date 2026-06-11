"""Bugungi yakunlangan sessiyalar — LIVE panelda kun oxirigacha saqlanadi."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from hub_day_log import HUB_DB_PATH

_DB = HUB_DB_PATH


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(_DB, timeout=15)
    c.row_factory = sqlite3.Row
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS live_finished_snapshots (
            day TEXT NOT NULL,
            session_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            finished_at TEXT NOT NULL,
            payload TEXT NOT NULL,
            PRIMARY KEY (day, session_id)
        )
        """
    )
    c.commit()
    return c


def save_finished_worker(*, day: str, snap: dict[str, Any]) -> None:
    sid = int(snap.get("session_id") or 0)
    uid = int(snap.get("user_id") or 0)
    finished_at = str(snap.get("finished_at") or "")
    if not day or not sid or not uid or not finished_at:
        return
    payload = json.dumps(snap, ensure_ascii=False)
    with _conn() as c:
        c.execute(
            """
            INSERT INTO live_finished_snapshots(day, session_id, user_id, finished_at, payload)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(day, session_id) DO UPDATE SET
                user_id = excluded.user_id,
                finished_at = excluded.finished_at,
                payload = excluded.payload
            """,
            (day, sid, uid, finished_at, payload),
        )
        c.commit()


def list_finished_workers(day: str) -> list[dict[str, Any]]:
    with _conn() as c:
        cur = c.execute(
            """
            SELECT payload FROM live_finished_snapshots
            WHERE day = ?
            ORDER BY finished_at DESC
            """,
            (day,),
        )
        out: list[dict[str, Any]] = []
        for row in cur.fetchall():
            try:
                snap = json.loads(row["payload"])
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
            if isinstance(snap, dict):
                out.append(snap)
        return out
