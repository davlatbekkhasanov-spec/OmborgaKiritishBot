"""Muhit o'zgaruvchilari."""

from __future__ import annotations

import os
from functools import lru_cache

_resolved_group_id: int | None = None


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
    raw = (raw or "").strip().strip('"').strip("'").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _resolve_group_id_from_env() -> int | None:
    for key in (
        "GROUP_ID",
        "GROUP_CHAT_ID",
        "CHAT_ID",
        "TELEGRAM_GROUP_ID",
    ):
        val = _parse_group_id(os.getenv(key) or "")
        if val is not None:
            return val
    return None


def get_group_id() -> int | None:
    if _resolved_group_id is not None:
        return _resolved_group_id
    return settings()["group_id"]


def set_resolved_group_id(group_id: int) -> None:
    global _resolved_group_id
    _resolved_group_id = int(group_id)


@lru_cache(maxsize=1)
def settings() -> dict:
    token = (os.getenv("BOT_TOKEN") or "").strip()
    group_id = _resolve_group_id_from_env()
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


def public_base_url() -> str:
    url = (os.getenv("PUBLIC_URL") or "").strip().rstrip("/")
    if url:
        return url
    domain = (os.getenv("RAILWAY_PUBLIC_DOMAIN") or "").strip()
    if domain:
        return f"https://{domain}"
    port = (os.getenv("PORT") or "8080").strip() or "8080"
    return f"http://localhost:{port}"


def startup_warnings() -> list[str]:
    s = settings()
    w: list[str] = []
    if not s["token"]:
        w.append("BOT_TOKEN yo'q")
    if not s["admin_ids"]:
        w.append("ADMIN_IDS yo'q — Boshlash hammaga ochiq (test)")
    if not s["group_id"]:
        w.append("GROUP_ID yo'q — faqat guruhdan Boshlash ishlaydi")
    from live_api import live_dash_token

    if not live_dash_token():
        w.append("LIVE_DASH_TOKEN yoki YORDAMCHI_HUB_SECRET yo'q — /live panel ishlamaydi")
    if not (os.getenv("PUBLIC_URL") or os.getenv("RAILWAY_PUBLIC_DOMAIN") or "").strip():
        w.append("PUBLIC_URL/RAILWAY_PUBLIC_DOMAIN yo'q — /live havola to'liq emas")
    return w
