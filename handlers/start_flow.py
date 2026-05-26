"""Har bir ishchi — yuk rasmi bilan mustaqil boshlash."""

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
from services.group_panel import ensure_group_panel, notify_session_change
from states import StartStates
from texts import BTN_START_MOVE
from ui import group_user_started_caption, he, photo_album_caption, session_started_card, start_photo_prompt

router = Router(name="start_flow")
log = logging.getLogger(__name__)


@router.message(F.text == BTN_START_MOVE, F.chat.type == ChatType.PRIVATE)
async def begin_start(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if not user:
        return
    ok, err = storage.try_begin_start(user.id)
    if not ok:
        return await message.answer(f"⚠️  {he(err)}", parse_mode="HTML")
    await state.set_state(StartStates.waiting_start_photo)
    await message.answer(start_photo_prompt(), parse_mode="HTML")


@router.message(Command("startmove"), F.chat.type == ChatType.PRIVATE)
async def cmd_startmove_alias(message: Message, state: FSMContext) -> None:
    await begin_start(message, state)


@router.message(StateFilter(StartStates.waiting_start_photo), F.photo)
async def start_photo_received(message: Message, state: FSMContext, bot: Bot) -> None:
    user = message.from_user
    if not user:
        return
    await state.clear()

    photo_id = message.photo[-1].file_id
    name = user.full_name or "Noma'lum"
    sess = storage.activate_session(user.id, name, photo_id)

    group_id = get_group_id() or settings()["group_id"]
    if group_id:
        try:
            await bot.send_photo(
                group_id,
                photo_id,
                caption=group_user_started_caption(
                    name=name, session_id=sess["id"]
                ),
                parse_mode="HTML",
            )
        except Exception as e:
            log.warning("Guruhga boshlash rasmi: %s", e)

    await ensure_group_panel(bot)
    await notify_session_change(bot)

    await message.answer(
        session_started_card(name=name, session_id=sess["id"]),
        parse_mode="HTML",
        reply_markup=private_keyboard_for(user.id),
    )


@router.message(StateFilter(StartStates.waiting_start_photo))
async def start_photo_invalid(message: Message) -> None:
    await message.answer(
        "⚠️  Faqat <b>foto</b> yuboring (yukingiz rasmi).",
        parse_mode="HTML",
    )


@router.message(Command("cancel"), StateFilter(StartStates))
async def start_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌  Boshlash bekor qilindi.", parse_mode="HTML")
