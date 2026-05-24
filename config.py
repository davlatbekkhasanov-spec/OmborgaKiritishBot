"""Muhit o'zgaruvchilari."""

from __future__ import annotations

import os
from functools import lru_cache


def _parse_ids(raw: str) -> frozenset[int]:
    out: set[int] = set()
    for part in (raw or "").replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.add(int(part))
        except ValueError:
            continue
    return frozenset(out)


def _parse_group_id(raw: str) -> int | None:
    raw = (raw or "").strip().strip('"').strip("'")
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


@lru_cache(maxsize=1)
def settings() -> dict:
    token = (os.getenv("BOT_TOKEN") or "").strip()
    group_id = _parse_group_id(
        os.getenv("GROUP_ID") or os.getenv("GROUP_CHAT_ID") or ""
    )
    admin_ids = _parse_ids(os.getenv("ADMIN_IDS") or os.getenv("ADMIN_ID") or "")
    tz = (os.getenv("TZ") or "Asia/Tashkent").strip() or "Asia/Tashkent"
    tick = max(3, int(os.getenv("TICK_SEC") or "5"))
    return {
        "token": token,
        "group_id": group_id,
        "admin_ids": admin_ids,
        "tz": tz,
        "tick_sec": tick,
    }


def is_admin(user_id: int | None) -> bool:
    if user_id is None:
        return False
    ids = settings()["admin_ids"]
    if not ids:
        return False
    return int(user_id) in ids


def startup_warnings() -> list[str]:
    s = settings()
    w: list[str] = []
    if not s["token"]:
        w.append("BOT_TOKEN yo'q")
    if not s["admin_ids"]:
        w.append("ADMIN_IDS yo'q — /startmove hammaga ochiq (test rejimi)")
    if not s["group_id"]:
        w.append("GROUP_ID yo'q — guruh xabarlari ishlamaydi")
    return w
