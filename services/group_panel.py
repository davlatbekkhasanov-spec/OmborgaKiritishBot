"""Guruh LIVE panelini yaratish va yangilash."""

from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

import app_context
import storage
from services.group_resolve import resolve_group_chat_id
from ui import group_live_card

log = logging.getLogger(__name__)


async def ensure_group_panel(bot: Bot) -> bool:
    """Birinchi ishchi boshlaganda guruhda LIVE xabar."""
    if storage.group_panel.get("message_id"):
        return True
    group_id = await resolve_group_chat_id(bot)
    if not group_id:
        return False
    try:
        sent = await bot.send_message(
            group_id,
            group_live_card(),
            parse_mode="HTML",
        )
        storage.group_panel["chat_id"] = group_id
        storage.group_panel["message_id"] = sent.message_id
        return True
    except Exception as e:
        log.warning("Guruh paneli ochilmadi: %s", e)
        return False


async def refresh_group_panel(bot: Bot) -> None:
    chat_id = storage.group_panel.get("chat_id")
    msg_id = storage.group_panel.get("message_id")
    if not chat_id or not msg_id:
        return
    if not storage.any_active_users():
        text = group_live_card(empty=True)
    else:
        text = group_live_card()
    try:
        await bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=msg_id,
            parse_mode="HTML",
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            log.warning("Panel yangilash: %s", e)


async def notify_session_change(bot: Bot) -> None:
    """Guruh paneli o'chirilgan — LIVE ma'lumot /live dashboardda."""
    if app_context.ticker:
        app_context.ticker.stop()
