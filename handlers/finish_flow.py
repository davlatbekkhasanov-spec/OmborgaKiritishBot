"""Yakunlash — tugma bosilganda darhol hisobot."""

from __future__ import annotations

import logging
from typing import Any

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message

import storage
from keyboards import private_keyboard_for
from services.group_panel import notify_session_change
from services.group_resolve import resolve_group_chat_id
from texts import BTN_FINISH
from integrations_compact import compact_session_summary
from ui import final_report_card, he
from yordamchi_push import push_to_yordamchi_hub_background

router = Router(name="finish")
log = logging.getLogger(__name__)


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
    return await _send_html(bot, group_id, header + report)


@router.message(F.text == BTN_FINISH, F.chat.type == ChatType.PRIVATE)
async def finish_from_private(message: Message, bot: Bot) -> None:
    uid = message.from_user.id if message.from_user else 0
    ok, err, sess = storage.finish_user_session(uid)
    if not ok or not sess:
        return await message.answer(f"⚠️  {he(err)}", parse_mode="HTML")

    report = final_report_card(sess)
    push_to_yordamchi_hub_background(
        tg_id=uid,
        bot_key="omborga",
        summary=compact_session_summary(sess),
    )
    group_ok = await _send_group_finish_report(bot, sess, report)
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


@router.message(Command("finish"), F.chat.type == ChatType.PRIVATE)
async def cmd_finish_alias(message: Message, bot: Bot) -> None:
    await finish_from_private(message, bot)
