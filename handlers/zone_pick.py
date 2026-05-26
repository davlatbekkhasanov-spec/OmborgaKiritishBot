"""Zona tanlash — shaxsiy chat."""

from __future__ import annotations

from aiogram import Bot

import app_context
import storage
from keyboards import zone_inline_keyboard
from ui import banner, he


async def send_trip_started(bot: Bot, chat_id: int, user_id: int) -> None:
    if not storage.has_active_session():
        await bot.send_message(
            chat_id,
            "⚠️  Hozircha jarayon yo'q. Mas'ul <b>Boshlash</b> ni bossin.",
            parse_mode="HTML",
        )
        return
    if not storage.is_participant(user_id):
        await bot.send_message(
            chat_id,
            "⚠️  Avval <b>guruhda</b> «Men qatnashaman» bosing.",
            parse_mode="HTML",
        )
        return

    ok, msg = storage.try_start_trip(user_id)
    if not ok:
        await bot.send_message(chat_id, f"⚠️  {he(msg)}", parse_mode="HTML")
        return

    if app_context.ticker:
        await app_context.ticker.refresh()

    bot_user = app_context.bot_username or "BOT"
    await bot.send_message(
        chat_id,
        f"{banner('REYS BOSHLANDI', icon='🚛')}\n\n"
        "1️⃣  Zonadagi <b>QR</b> ni telefon kamerasi bilan skaner qiling\n"
        f"    <code>t.me/{he(bot_user)}?start=zone_...</code>\n\n"
        "2️⃣  Yoki pastdagi <b>Zonani tanlash</b> tugmasi",
        parse_mode="HTML",
        reply_markup=zone_inline_keyboard(),
    )


async def send_zone_picker(bot: Bot, chat_id: int, user_id: int) -> None:
    if not storage.is_participant(user_id):
        await bot.send_message(
            chat_id,
            "⚠️  Avval <b>guruhda</b> «Men qatnashaman» bosing.",
            parse_mode="HTML",
        )
        return
    if user_id not in storage.active_trips:
        await bot.send_message(
            chat_id,
            "⚠️  Avval <b>📦 Reys oldim</b> bosing.",
            parse_mode="HTML",
        )
        return
    await bot.send_message(
        chat_id,
        "📦  <b>Zonani tanlang</b> — bitta bosish:",
        parse_mode="HTML",
        reply_markup=zone_inline_keyboard(),
    )
