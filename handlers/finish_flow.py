"""Yakunlash — suratlar va final hisobot."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import app_context
from config import get_group_id, settings
import storage
from keyboards import CB_FINISH
from states import FinishStates
from texts import BTN_FINISH
from ui import final_report_card, photo_album_caption, photo_prompt

router = Router(name="finish")


async def begin_finish(user_id: int, bot: Bot, state: FSMContext) -> str | None:
    """
  Yakunlashni boshlaydi.
  Muvaffaqiyat: None qaytaradi.
  Xato: foydalanuvchiga matn.
    """
    if not storage.has_active_session():
        return "⚠️  Aktiv jarayon yo'q. Avval <b>Boshlash</b> bosing."
    if not storage.can_manage(user_id):
        return "⛔  <b>Yakunlash</b> faqat mas'ul/admin uchun."
    if storage.active_trips:
        return "⚠️  Ochiq reyslar bor — avval QR skaner qiling."

    storage.active_session["status"] = "finishing"
    if app_context.ticker:
        app_context.ticker.stop()

    await state.set_state(FinishStates.waiting_ombor_photo)
    try:
        await bot.send_message(
            user_id,
            photo_prompt(
                1,
                2,
                "Omborga olib kirilgan yuklar",
                "Yuklar ombor ichida joylashganini ko'rsating",
            ),
            parse_mode="HTML",
        )
    except Exception:
        return (
            "Bot bilan shaxsiy chatda /start bosing, "
            "keyin qayta <b>Yakunlash</b> tugmasini bosing."
        )
    return None


@router.callback_query(F.data == CB_FINISH)
async def finish_from_group(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    user = callback.from_user
    if not user:
        return
    err = await begin_finish(user.id, bot, state)
    if err:
        await callback.answer(err.replace("<b>", "").replace("</b>", ""), show_alert=True)
        return
    await callback.answer()


@router.message(F.text == BTN_FINISH)
async def finish_from_private(message: Message, state: FSMContext, bot: Bot) -> None:
    uid = message.from_user.id if message.from_user else 0
    err = await begin_finish(uid, bot, state)
    if err:
        await message.answer(err, parse_mode="HTML")


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
    group_id = get_group_id() or settings()["group_id"]

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
