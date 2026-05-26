"""Yakunlash — faqat o'z sessiyasi."""

from __future__ import annotations

import logging
from typing import Any

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import storage
from keyboards import private_keyboard_for
from services.group_panel import notify_session_change
from services.group_resolve import resolve_group_chat_id
from states import FinishStates
from texts import BTN_FINISH
from ui import final_report_card, he, photo_album_caption, photo_prompt

router = Router(name="finish")
log = logging.getLogger(__name__)


async def begin_finish(user_id: int, bot: Bot, state: FSMContext) -> str | None:
    ok, err = storage.begin_user_finish(user_id)
    if not ok:
        return f"⚠️  {err}"

    await state.set_state(FinishStates.waiting_bosh_joy_photo)
    await state.update_data(finish_user_id=user_id)
    try:
        await bot.send_message(
            user_id,
            photo_prompt(
                1,
                1,
                "Tashqaridagi bo'sh joy",
                "Yuk olib kirilgach tashqarida bo'sh qolgan joy",
            ),
            parse_mode="HTML",
        )
    except Exception:
        storage.cancel_user_finish(user_id)
        await state.clear()
        return "Avval botda /start bosing."
    return None


async def _send_html(bot: Bot, chat_id: int, text: str) -> bool:
    try:
        await bot.send_message(chat_id, text, parse_mode="HTML")
        return True
    except TelegramBadRequest as e:
        log.warning("HTML xabar yuborilmadi (%s): %s", chat_id, e)
        try:
            await bot.send_message(chat_id, text)
            return True
        except Exception as e2:
            log.error("Matn ham yuborilmadi: %s", e2)
            return False


async def _send_group_finish_report(bot: Bot, sess: dict[str, Any], report: str) -> bool:
    group_id = await resolve_group_chat_id(
        bot, prefer=sess.get("group_chat_id")
    )
    if not group_id:
        log.error("Guruh ID yo'q — hisobot guruhga ketmadi")
        return False

    name = sess.get("full_name") or "Noma'lum"
    header = f"🏁  <b>{he(name)}</b> ishini yakunladi\n\n"
    ok = await _send_html(bot, group_id, header + report)

    if sess.get("start_photo"):
        try:
            await bot.send_photo(
                group_id,
                sess["start_photo"],
                caption=photo_album_caption("start", worker_name=name),
                parse_mode="HTML",
            )
        except Exception as e:
            log.warning("Boshlash rasmi guruhga: %s", e)

    fid = (sess.get("finish_photos") or {}).get("bosh_joy")
    if fid:
        try:
            await bot.send_photo(
                group_id,
                fid,
                caption=photo_album_caption("bosh_joy", worker_name=name),
                parse_mode="HTML",
            )
        except Exception as e:
            log.warning("Surat bosh_joy guruhga: %s", e)

    return ok


@router.message(F.text == BTN_FINISH, F.chat.type == ChatType.PRIVATE)
async def finish_from_private(message: Message, state: FSMContext, bot: Bot) -> None:
    uid = message.from_user.id if message.from_user else 0
    err = await begin_finish(uid, bot, state)
    if err:
        await message.answer(err, parse_mode="HTML")


@router.message(StateFilter(FinishStates.waiting_bosh_joy_photo), F.photo)
async def finish_bosh_joy(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    uid = data.get("finish_user_id") or (message.from_user.id if message.from_user else 0)
    s = storage.get_session(uid)
    if not s:
        await state.clear()
        return await message.answer("⚠️  Sessiya topilmadi.", parse_mode="HTML")

    s.setdefault("finish_photos", {})["bosh_joy"] = message.photo[-1].file_id
    await state.clear()

    report = final_report_card(s)
    group_ok = await _send_group_finish_report(bot, s, report)

    storage.end_user_session(uid)
    await notify_session_change(bot)

    extra = ""
    if not group_ok:
        extra = (
            "\n\n⚠️  <i>Guruhga yuborib bo'lmadi. "
            "/guruh va GROUP_ID ni tekshiring.</i>"
        )

    await message.answer(
        report + extra,
        parse_mode="HTML",
        reply_markup=private_keyboard_for(uid),
    )


@router.message(Command("cancel"), StateFilter(FinishStates))
async def finish_cancel(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    uid = data.get("finish_user_id") or (message.from_user.id if message.from_user else 0)
    await state.clear()
    storage.cancel_user_finish(uid)
    await notify_session_change(bot)
    await message.answer(
        "❌  Yakunlash bekor.\nJarayoningiz davom etmoqda.",
        parse_mode="HTML",
        reply_markup=private_keyboard_for(uid),
    )
