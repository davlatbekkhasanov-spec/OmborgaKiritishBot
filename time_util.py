"""Vaqt formatlash."""

from __future__ import annotations

from datetime import datetime


def fmt_hm(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def fmt_elapsed(join_time: datetime, now: datetime | None = None) -> str:
    """00:03:21"""
    now = now or datetime.now()
    sec = max(0, int((now - join_time).total_seconds()))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"
