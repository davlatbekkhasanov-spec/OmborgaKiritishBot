"""Yakunlash — suratlar va final hisobot."""

from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import app_context
import storage
from states import FinishStates
from texts import BTN_FINISH
from ui import final_report_card, group_session_closed_card, photo_album_caption, photo_prompt

router = Router(name="finish")
log = logging.getLogger(__name__)


async def _close_group_live_panel(bot: Bot) -> None:
    sess = storage.active_session
    if not sess:
        return
    chat_id = sess.get("group_chat_id")
    msg_id = sess.get("group_message_id")
    if not chat_id or not msg_id:
        return
    try:
        await bot.edit_message_text(
            group_session_closed_card(),
            chat_id=chat_id,
            message_id=msg_id,
            parse_mode="HTML",
            reply_markup=None,
        )
    except Exception as e:
        log.warning("Guruh panelini yopish: %s", e)


async def begin_finish(user_id: int, bot: Bot, state: FSMContext) -> str | None:
    if not storage.has_active_session():
        return "⚠️  Aktiv jarayon yo'q. Avval <b>Boshlash</b> bosing."
    if not storage.can_manage(user_id):
        return "⛔  <b>Yakunlash</b> faqat mas'ul/admin uchun."
    if storage.active_trips:
        n = len(storage.active_trips)
        return (
            f"⚠️  <b>{n}</b> ta ochiq reys bor — avval yakunlang "
            "(QR yoki Zonani tanlash)."
        )

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


@router.message(F.text == BTN_FINISH, F.chat.type == ChatType.PRIVATE)
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
    sess = storage.active_session
    group_id = (sess or {}).get("group_chat_id")

    if group_id:
        await bot.send_message(group_id, report, parse_mode="HTML")
        for key in ("ombor", "bosh_joy"):
            fid = storage.photos.get(key)
            if fid:
                await bot.send_photo(
                    group_id,
                    fid,
                    caption=photo_album_caption(key),
                    parse_mode="HTML",
                )

    await _close_group_live_panel(bot)
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
