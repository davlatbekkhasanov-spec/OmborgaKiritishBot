"""QR deep link — zone skaner."""

from __future__ import annotations

from aiogram import Bot
from aiogram.types import Message

import app_context
import storage
from ui import trip_complete_card


async def handle_zone_scan(message: Message, bot: Bot, zone_code: str) -> None:
    user = message.from_user
    if not user:
        return

    ok, result = storage.try_complete_trip(user.id, zone_code)
    if not ok:
        from ui import he

        await message.answer(f"⚠️  {he(result)}", parse_mode="HTML")
        return

    record = result
    name = user.full_name or "Noma'lum"
    await message.answer(
        trip_complete_card(
            zone_name=record["zone_name"],
            distance_meter=record["distance_meter"],
            duration_sec=record["duration_sec"],
            worker_name=name,
        ),
        parse_mode="HTML",
    )

    if app_context.ticker:
        await app_context.ticker.refresh()
