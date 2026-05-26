"""Ishchi — shaxsiy chat."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.types import CallbackQuery, Message

import storage
from handlers.qr import complete_zone_for_user
from handlers.zone_pick import send_trip_started, send_zone_picker
from keyboards import CB_ZONE_PREFIX, private_keyboard_for
from services.group_panel import notify_session_change
from texts import BTN_BREAK_END, BTN_BREAK_START, BTN_PICK_ZONE, BTN_TRIP
from time_util import fmt_duration_short
from ui import banner, he

router = Router(name="private_worker")


@router.message(F.text == BTN_TRIP, F.chat.type == ChatType.PRIVATE)
async def cmd_trip_private(message: Message, bot: Bot) -> None:
    user = message.from_user
    if not user:
        return
    await send_trip_started(bot, message.chat.id, user.id)


@router.message(F.text == BTN_BREAK_START, F.chat.type == ChatType.PRIVATE)
async def cmd_break_start(message: Message) -> None:
    user = message.from_user
    if not user:
        return
    ok, msg = storage.try_start_break(user.id)
    await message.answer(
        f"{'☕' if ok else '⚠️'}  {he(msg)}",
        parse_mode="HTML",
        reply_markup=private_keyboard_for(user.id),
    )
    if ok:
        await message.answer(
            f"{banner('DAM', icon='☕')}\n\n"
            "Tayyor bo'lgach <b>Davom etish</b> bosing.\n"
            "Keyin yangi reys.",
            parse_mode="HTML",
        )


@router.message(F.text == BTN_BREAK_END, F.chat.type == ChatType.PRIVATE)
async def cmd_break_end(message: Message, bot: Bot) -> None:
    user = message.from_user
    if not user:
        return
    ok, result = storage.try_end_break(user.id)
    if not ok:
        await message.answer(f"⚠️  {he(result)}", parse_mode="HTML")
        return
    sec = int(result)
    await notify_session_change(bot)
    await message.answer(
        f"▶️  <b>Davom etish</b>\n\n"
        f"Dam: <b>{fmt_duration_short(sec)}</b>\n\n"
        f"Endi <b>{he(BTN_TRIP)}</b> bosing.",
        parse_mode="HTML",
        reply_markup=private_keyboard_for(user.id),
    )


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
