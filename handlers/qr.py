"""Zona tanlash / QR havola — reysni yopish."""

from __future__ import annotations

from aiogram import Bot
from aiogram.types import Message

import app_context
import storage
from ui import he, trip_complete_card


async def complete_trip_for_user(
    *,
    bot: Bot,
    user_id: int,
    full_name: str,
    zone_code: str,
    chat_id: int,
) -> None:
    ok, result = storage.try_complete_trip(user_id, zone_code)
    if not ok:
        await bot.send_message(chat_id, f"⚠️  {he(result)}", parse_mode="HTML")
        return

    record = result
    await bot.send_message(
        chat_id,
        trip_complete_card(
            zone_name=record["zone_name"],
            distance_meter=record["distance_meter"],
            duration_sec=record["duration_sec"],
            worker_name=full_name or "Noma'lum",
        ),
        parse_mode="HTML",
    )
    if app_context.ticker:
        await app_context.ticker.refresh()


async def handle_zone_scan(message: Message, bot: Bot, zone_code: str) -> None:
    user = message.from_user
    if not user:
        return
    await complete_trip_for_user(
        bot=bot,
        user_id=user.id,
        full_name=user.full_name or "Noma'lum",
        zone_code=zone_code,
        chat_id=message.chat.id,
    )
