"""Har bir ishchi — Boshlash tugmasi bilan mustaqil boshlash."""

from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message

import storage
from keyboards import private_keyboard_for
from services.group_resolve import resolve_group_chat_id
from texts import BTN_START_MOVE
from ui import group_carrying_started, he, session_started_card

router = Router(name="start_flow")
log = logging.getLogger(__name__)


async def _activate_and_notify(
    bot: Bot, user_id: int, name: str, *, reply_chat_id: int
) -> None:
    sess = storage.activate_session(user_id, name)

    group_id = await resolve_group_chat_id(bot)
    if group_id:
        sess["group_chat_id"] = group_id
        try:
            await bot.send_message(
                group_id,
                group_carrying_started(name=name),
                parse_mode="HTML",
            )
        except Exception as e:
            log.warning("Guruhga boshlash xabari: %s", e)
    else:
        log.warning("Guruh ID topilmadi — boshlash faqat shaxsiy chatda")

    await bot.send_message(
        reply_chat_id,
        session_started_card(name=name, session_id=sess["id"]),
        parse_mode="HTML",
        reply_markup=private_keyboard_for(user_id),
    )


@router.message(F.text == BTN_START_MOVE, F.chat.type == ChatType.PRIVATE)
async def begin_start(message: Message, bot: Bot) -> None:
    user = message.from_user
    if not user:
        return
    ok, err = storage.try_begin_start(user.id)
    if not ok:
        return await message.answer(f"⚠️  {he(err)}", parse_mode="HTML")
    await _activate_and_notify(
        bot, user.id, user.full_name or "Noma'lum", reply_chat_id=message.chat.id
    )


@router.message(Command("startmove"), F.chat.type == ChatType.PRIVATE)
async def cmd_startmove_alias(message: Message, bot: Bot) -> None:
    await begin_start(message, bot)
