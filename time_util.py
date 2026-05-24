"""Vaqt formatlash."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from config import settings


def _tz() -> ZoneInfo:
    try:
        return ZoneInfo(settings()["tz"])
    except Exception:
        return ZoneInfo("Asia/Tashkent")


def now_dt() -> datetime:
    return datetime.now(_tz())


def display_now() -> str:
    return now_dt().strftime("%d.%m.%Y  %H:%M")


def fmt_hm(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def fmt_elapsed(join_time: datetime, now: datetime | None = None) -> str:
    now = now or now_dt()
    sec = max(0, int((now - join_time).total_seconds()))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def fmt_duration(sec: int) -> str:
    sec = max(0, int(sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h} soat {m:02d} daq"
    if m:
        return f"{m} daq {s:02d} son"
    return f"{s} son"


def fmt_duration_short(sec: int) -> str:
    sec = max(0, int(sec))
    m, s = divmod(sec, 60)
    return f"{m}:{s:02d}"


def fmt_distance_m(meters: int) -> str:
    m = max(0, int(meters))
    if m >= 1000:
        return f"{m / 1000:.1f} km"
    return f"{m}m"
