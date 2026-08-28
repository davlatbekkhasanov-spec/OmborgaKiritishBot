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
from services.group_resolve import resolve_group_chat_id
from texts import BTN_FINISH
from integrations_compact import compact_session_summary
from ui import final_report_card, group_carrying_stopped, he
from hub_day_log import save_today_push
from live_api import snapshot_finished_worker
from live_day_store import save_finished_worker
from time_util import now_dt
from yordamchi_push import (
    push_session_end_background,
    push_to_yordamchi_hub,
    push_to_yordamchi_hub_background,
    today_iso,
)

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


async def _send_group_carrying_stopped(bot: Bot, sess: dict[str, Any]) -> bool:
    group_id = await resolve_group_chat_id(bot, prefer=sess.get("group_chat_id"))
    if not group_id:
        log.error("Guruh ID yo'q — tugatish xabari ketmadi")
        return False
    name = sess.get("full_name") or "Noma'lum"
    return await _send_html(bot, group_id, group_carrying_stopped(name=name))


@router.message(F.text == BTN_FINISH, F.chat.type == ChatType.PRIVATE)
async def finish_from_private(message: Message, bot: Bot) -> None:
    uid = message.from_user.id if message.from_user else 0
    ok, err, sess = storage.finish_user_session(uid)
    if not ok or not sess:
        return await message.answer(f"⚠️  {he(err)}", parse_mode="HTML")

    finished_at = now_dt()
    report = final_report_card(sess, finished_at=finished_at)
    hub_summary = compact_session_summary(sess)
    day = today_iso()
    save_finished_worker(day=day, snap=snapshot_finished_worker(sess, finished_at=finished_at))
    save_today_push(day=day, tg_id=uid, summary=hub_summary)
    ok, via = await push_to_yordamchi_hub(
        tg_id=uid,
        bot_key="omborga",
        summary=hub_summary,
        day_iso=day,
    )
    if not ok:
        log.warning("omborga hub push failed uid=%s via=%s", uid, via)
        push_to_yordamchi_hub_background(
            tg_id=uid,
            bot_key="omborga",
            summary=hub_summary,
            day_iso=day,
        )
    push_session_end_background(tg_id=uid, bot_key="omborga", activity_type="omborga")
    group_ok = await _send_group_carrying_stopped(bot, sess)

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
