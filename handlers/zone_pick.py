"""Zonani tanlash — inline tugmalar."""

from __future__ import annotations

from aiogram import Bot

from handlers.qr import complete_trip_for_user
from keyboards import zone_inline_keyboard


async def send_zone_picker(bot: Bot, chat_id: int, user_id: int) -> None:
    from storage import active_trips

    if user_id not in active_trips:
        await bot.send_message(
            chat_id,
            "⚠️  Avval guruhda <b>Reys oldim</b> bosing.",
            parse_mode="HTML",
        )
        return
    await bot.send_message(
        chat_id,
        "📍  <b>Zonani tanlang</b> — bitta bosish:",
        parse_mode="HTML",
        reply_markup=zone_inline_keyboard(),
    )


async def pick_zone_from_callback(bot: Bot, user_id: int, full_name: str, chat_id: int, zone_code: str) -> None:
    await complete_trip_for_user(
        bot=bot,
        user_id=user_id,
        full_name=full_name,
        zone_code=zone_code,
        chat_id=chat_id,
    )
