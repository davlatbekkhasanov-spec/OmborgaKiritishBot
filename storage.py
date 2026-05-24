"""RAM — 1-bosqich (SQLite keyinroq)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

# Faol jarayon yoki None
active_session: dict[str, Any] | None = None

# user_id -> {full_name, join_time, user_id}
participants: dict[int, dict[str, Any]] = {}

# 2-bosqich uchun joy
trips: dict[int, dict[str, Any]] = {}


def reset_session() -> None:
    global active_session, participants, trips
    active_session = None
    participants.clear()
    trips.clear()


def has_active_session() -> bool:
    return active_session is not None
