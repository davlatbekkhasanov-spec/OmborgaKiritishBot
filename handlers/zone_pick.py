"""Zona tanlash — shaxsiy chat."""

from __future__ import annotations

from aiogram import Bot

import app_context
import storage
from keyboards import zone_inline_keyboard
from services.group_panel import notify_session_change
from texts import BTN_START_MOVE
from ui import banner, he


async def send_trip_started(bot: Bot, chat_id: int, user_id: int) -> None:
    ok, msg = storage.try_start_trip(user_id)
    if not ok:
        await bot.send_message(chat_id, f"⚠️  {he(msg)}", parse_mode="HTML")
        return

    await notify_session_change(bot)
    bot_user = app_context.bot_username or "BOT"
    extra = ""
    if "\n\n" in msg:
        extra = f"\n\n{he(msg.split('\n\n', 1)[1])}"
    await bot.send_message(
        chat_id,
        f"{banner('REYS BOSHLANDI', icon='🚛')}\n\n"
        "1️⃣  Zonadagi <b>QR</b> yoki <b>NFC</b>\n"
        f"    <code>t.me/{he(bot_user)}?start=zone_...</code>\n\n"
        "2️⃣  Yoki <b>Zonani tanlash</b>\n\n"
        "<i>📏 Yuk bilan manzilgacha masofa</i>\n"
        "<i>Keyingi «Reys oldim»gacha — dam va yuksiz yurish avto</i>"
        f"{extra}",
        parse_mode="HTML",
        reply_markup=zone_inline_keyboard(),
    )


async def send_zone_picker(bot: Bot, chat_id: int, user_id: int) -> None:
    if not storage.has_user_session(user_id):
        await bot.send_message(
            chat_id,
            f"⚠️  Avval <b>{he(BTN_START_MOVE)}</b> bosing.",
            parse_mode="HTML",
        )
        return
    if not storage.user_has_open_trip(user_id):
        await bot.send_message(
            chat_id,
            "⚠️  Avval <b>📦 Reys oldim</b> bosing.",
            parse_mode="HTML",
        )
        return
    await bot.send_message(
        chat_id,
        "📦  <b>Zonani tanlang</b>:",
        parse_mode="HTML",
        reply_markup=zone_inline_keyboard(),
    )
