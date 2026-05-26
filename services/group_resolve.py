"""Ishlayotgan guruh chat ID ni topish."""

from __future__ import annotations

import logging

from aiogram import Bot

import storage
from config import get_group_id, settings
from services.group_check import GroupConfigError, group_id_candidates, verify_group_access

log = logging.getLogger(__name__)


def group_id_from_storage() -> int | None:
    """Panel yoki verify orqali saqlangan ID."""
    panel_cid = storage.group_panel.get("chat_id")
    if panel_cid:
        return int(panel_cid)
    gid = get_group_id() or settings()["group_id"]
    return int(gid) if gid else None


async def resolve_group_chat_id(bot: Bot, *, prefer: int | None = None) -> int | None:
    """
    Guruh ID: sessiya → panel → env → verify_group_access.
    Supergroup -100 format nomzodlari bilan sinash.
    """
    if prefer:
        for cid in group_id_candidates(int(prefer)):
            try:
                await bot.get_chat(cid)
                storage.group_panel["chat_id"] = cid
                return cid
            except Exception:
                continue

    gid = group_id_from_storage()
    if gid:
        for cid in group_id_candidates(gid):
            try:
                await bot.get_chat(cid)
                storage.group_panel["chat_id"] = cid
                return cid
            except Exception:
                continue

    try:
        await verify_group_access(bot)
        return group_id_from_storage()
    except GroupConfigError as e:
        log.warning("Guruh ID topilmadi: %s", e)
        return None
