"""Ishchi — faqat shaxsiy chat."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.types import CallbackQuery, Message

from handlers.qr import complete_zone_for_user
from handlers.zone_pick import send_trip_started, send_zone_picker
from keyboards import CB_ZONE_PREFIX
from texts import BTN_PICK_ZONE, BTN_TRIP

router = Router(name="private_worker")


@router.message(F.text == BTN_TRIP, F.chat.type == ChatType.PRIVATE)
async def cmd_trip_private(message: Message, bot: Bot) -> None:
    user = message.from_user
    if not user:
        return
    await send_trip_started(bot, message.chat.id, user.id)


@router.message(F.text == BTN_PICK_ZONE, F.chat.type == ChatType.PRIVATE)
async def cmd_pick_zone(message: Message, bot: Bot) -> None:
    user = message.from_user
    if not user:
        return
    await send_zone_picker(bot, message.chat.id, user.id)


@router.callback_query(
    F.data.startswith(CB_ZONE_PREFIX),
    F.message.chat.type == ChatType.PRIVATE,
)
async def on_zone_private(callback: CallbackQuery, bot: Bot) -> None:
    user = callback.from_user
    if not user or not callback.data or not callback.message:
        return
    zone_code = callback.data[len(CB_ZONE_PREFIX) :]
    ok = await complete_zone_for_user(
        bot,
        callback.message.chat.id,
        user.id,
        user.full_name or "Noma'lum",
        zone_code,
        auto_start_trip=False,
    )
    await callback.answer(
        "✅ Reys yopildi" if ok else "⚠️ Avval Reys oldim bosing",
        show_alert=not ok,
    )
