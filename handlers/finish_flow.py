"""Yakunlash — suratlar va final hisobot."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import app_context
from config import settings
import storage
from keyboards import CB_FINISH
from states import FinishStates
from ui import final_report_card, photo_album_caption, photo_prompt

router = Router(name="finish")


@router.callback_query(F.data == CB_FINISH)
async def finish_start(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    user = callback.from_user
    if not user:
        return
    if not storage.has_active_session():
        await callback.answer("Jarayon aktiv emas.", show_alert=True)
        return
    if not storage.can_manage(user.id):
        await callback.answer("Faqat mas'ul/admin.", show_alert=True)
        return
    if storage.active_trips:
        await callback.answer("Ochiq reyslar bor.", show_alert=True)
        return

    storage.active_session["status"] = "finishing"
    if app_context.ticker:
        app_context.ticker.stop()
    await callback.answer()

    await state.set_state(FinishStates.waiting_ombor_photo)
    try:
        await bot.send_message(
            user.id,
            photo_prompt(
                1,
                2,
                "Omborga olib kirilgan yuklar",
                "Yuklar ombor ichida joylashganini ko'rsating",
            ),
            parse_mode="HTML",
        )
    except Exception:
        if callback.message:
            await callback.message.answer(
                "Shaxsiy chatda botni /start qiling, keyin qayta «Yakunlash».",
            )


@router.message(StateFilter(FinishStates.waiting_ombor_photo), F.photo)
async def finish_ombor(message: Message, state: FSMContext) -> None:
    storage.photos["ombor"] = message.photo[-1].file_id
    await state.set_state(FinishStates.waiting_bosh_joy_photo)
    await message.answer(
        photo_prompt(
            2,
            2,
            "Tashqaridagi bo'sh joy",
            "Yuk olib kirilgach tashqarida bo'sh qolgan joy",
        ),
        parse_mode="HTML",
    )


@router.message(StateFilter(FinishStates.waiting_bosh_joy_photo), F.photo)
async def finish_bosh_joy(message: Message, state: FSMContext, bot: Bot) -> None:
    storage.photos["bosh_joy"] = message.photo[-1].file_id
    await state.clear()

    report = final_report_card()
    group_id = settings()["group_id"]

    if group_id:
        await bot.send_message(group_id, report, parse_mode="HTML")
        for key in ("ombor", "bosh_joy", "boshlangich"):
            fid = storage.photos.get(key)
            if fid:
                await bot.send_photo(
                    group_id,
                    fid,
                    caption=photo_album_caption(key),
                    parse_mode="HTML",
                )

    await message.answer(report, parse_mode="HTML")
    storage.reset_session()


@router.message(Command("cancel"), StateFilter(FinishStates))
async def finish_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    if storage.active_session:
        storage.active_session["status"] = "active"
        if app_context.ticker:
            await app_context.ticker.start()
    await message.answer(
        "❌  Yakunlash bekor qilindi.\nJarayon <b>LIVE</b> davom etmoqda.",
        parse_mode="HTML",
    )
