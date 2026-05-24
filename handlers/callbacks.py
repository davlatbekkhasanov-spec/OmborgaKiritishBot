"""Guruh inline tugmalar."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

import app_context
import storage
from keyboards import CB_JOIN, CB_TRIP
from ui import trip_started_card

router = Router(name="callbacks")


@router.callback_query(F.data == CB_JOIN)
async def on_join(callback: CallbackQuery) -> None:
    user = callback.from_user
    if not user:
        return
    ok, msg = storage.try_join(user.id, user.full_name or "Noma'lum")
    await callback.answer(msg, show_alert=not ok)
    if ok and app_context.ticker:
        await app_context.ticker.refresh()


@router.callback_query(F.data == CB_TRIP)
async def on_trip(callback: CallbackQuery, bot: Bot) -> None:
    user = callback.from_user
    if not user:
        return
    ok, msg = storage.try_start_trip(user.id)
    await callback.answer(msg, show_alert=not ok)
    if not ok:
        return
    if app_context.ticker:
        await app_context.ticker.refresh()
    try:
        from texts import BTN_QR_SCAN

        await bot.send_message(
            user.id,
            trip_started_card(bot_username=app_context.bot_username)
            + f"\n\n📷  Yoki shaxsiy chatda <b>{BTN_QR_SCAN}</b> tugmasini bosing.",
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    except Exception:
        await callback.answer(
            "Bot bilan shaxsiy chatda /start bosing.",
            show_alert=True,
        )
