"""Yakunlash — faqat o'z sessiyasi."""

from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import storage
from config import get_group_id, settings
from keyboards import private_keyboard_for
from services.group_panel import notify_session_change
from states import FinishStates
from texts import BTN_FINISH
from ui import final_report_card, photo_album_caption, photo_prompt

router = Router(name="finish")
log = logging.getLogger(__name__)


async def begin_finish(user_id: int, bot: Bot, state: FSMContext) -> str | None:
    ok, err = storage.begin_user_finish(user_id)
    if not ok:
        return f"⚠️  {err}"

    await state.set_state(FinishStates.waiting_ombor_photo)
    await state.update_data(finish_user_id=user_id)
    try:
        await bot.send_message(
            user_id,
            photo_prompt(
                1,
                2,
                "Omborga olib kirilgan yuklar",
                "Siz olib kirgan yuklar omborda",
            ),
            parse_mode="HTML",
        )
    except Exception:
        storage.cancel_user_finish(user_id)
        await state.clear()
        return "Avval botda /start bosing."
    return None


@router.message(F.text == BTN_FINISH, F.chat.type == ChatType.PRIVATE)
async def finish_from_private(message: Message, state: FSMContext, bot: Bot) -> None:
    uid = message.from_user.id if message.from_user else 0
    err = await begin_finish(uid, bot, state)
    if err:
        await message.answer(err, parse_mode="HTML")


@router.message(StateFilter(FinishStates.waiting_ombor_photo), F.photo)
async def finish_ombor(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    uid = data.get("finish_user_id") or (message.from_user.id if message.from_user else 0)
    s = storage.get_session(uid)
    if not s:
        await state.clear()
        return await message.answer("⚠️  Sessiya topilmadi.", parse_mode="HTML")
    s.setdefault("finish_photos", {})["ombor"] = message.photo[-1].file_id
    await state.set_state(FinishStates.waiting_bosh_joy_photo)
    await message.answer(
        photo_prompt(2, 2, "Tashqaridagi bo'sh joy", "Yuk olib kirilgandan keyin bo'sh qolgan joy"),
        parse_mode="HTML",
    )


@router.message(StateFilter(FinishStates.waiting_bosh_joy_photo), F.photo)
async def finish_bosh_joy(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    uid = data.get("finish_user_id") or (message.from_user.id if message.from_user else 0)
    s = storage.get_session(uid)
    if not s:
        await state.clear()
        return
    s.setdefault("finish_photos", {})["bosh_joy"] = message.photo[-1].file_id
    await state.clear()

    name = s["full_name"]
    report = final_report_card(s)
    group_id = get_group_id() or settings()["group_id"]

    if group_id:
        await bot.send_message(
            group_id,
            f"🏁  <b>{name}</b> ishini yakunladi\n\n{report}",
            parse_mode="HTML",
        )
        if s.get("start_photo"):
            await bot.send_photo(
                group_id,
                s["start_photo"],
                caption=photo_album_caption("start", worker_name=name),
                parse_mode="HTML",
            )
        for key in ("ombor", "bosh_joy"):
            fid = (s.get("finish_photos") or {}).get(key)
            if fid:
                await bot.send_photo(
                    group_id,
                    fid,
                    caption=photo_album_caption(key, worker_name=name),
                    parse_mode="HTML",
                )

    storage.end_user_session(uid)
    await notify_session_change(bot)

    await message.answer(
        report,
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
