"""Guruh va zona callbacklari."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

import app_context
import storage
from handlers.zone_pick import pick_zone_from_callback, send_zone_picker
from keyboards import CB_JOIN, CB_TRIP, CB_ZONE_PREFIX, zone_inline_keyboard
from ui import banner

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
        await bot.send_message(
            user.id,
            f"{banner('REYS BOSHLANDI', icon='🚛')}\n\n"
            "👇  Zonani tanlang:",
            parse_mode="HTML",
            reply_markup=zone_inline_keyboard(),
        )
    except Exception:
        await callback.answer(
            "Shaxsiy chatda /start bosing, keyin «Zonani tanlash».",
            show_alert=True,
        )


@router.callback_query(F.data.startswith(CB_ZONE_PREFIX))
async def on_zone_button(callback: CallbackQuery, bot: Bot) -> None:
    user = callback.from_user
    if not user or not callback.data:
        return
    zone_code = callback.data[len(CB_ZONE_PREFIX) :]
    chat_id = callback.message.chat.id if callback.message else user.id

    await pick_zone_from_callback(
        bot,
        user.id,
        user.full_name or "Noma'lum",
        chat_id,
        zone_code,
    )
    await callback.answer("✅")
