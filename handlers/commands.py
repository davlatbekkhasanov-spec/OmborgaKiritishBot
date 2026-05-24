"""Buyruqlar."""

from __future__ import annotations

from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

import app_context
from config import is_admin, settings
import storage
from keyboards import group_live_keyboard
from ui import group_live_card, welcome_card, worker_hint_card, zones_list_card
from time_util import fmt_hm, now_dt

router = Router(name="commands")


async def cmd_start(message: Message, command: CommandObject, bot: Bot) -> None:
    zone = storage.parse_zone_payload(command.args)
    if zone:
        from handlers.qr import handle_zone_scan

        await handle_zone_scan(message, bot, zone)
        return

    user = message.from_user
    name = user.full_name if user else "Mehmon"
    uid = user.id if user else 0
    if is_admin(uid):
        text = welcome_card(is_masul=True, name=name)
    else:
        text = worker_hint_card()
    await message.answer(text, parse_mode="HTML")


async def cmd_zones(message: Message) -> None:
    await message.answer(
        zones_list_card(bot_username=app_context.bot_username),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


async def cmd_id(message: Message) -> None:
    await message.answer(
        f"📌  <b>Chat ID</b>\n<code>{message.chat.id}</code>",
        parse_mode="HTML",
    )


async def cmd_startmove(message: Message, bot: Bot) -> None:
    uid = message.from_user.id if message.from_user else 0
    cfg = settings()

    if cfg["admin_ids"] and not is_admin(uid):
        return await message.answer(
            "⛔  Faqat <b>mas'ul/admin</b> jarayonni boshlaydi.",
            parse_mode="HTML",
        )

    if storage.has_active_session():
        return await message.answer(
            "⚠️  Aktiv jarayon bor. Avval <b>Yakunlash</b>.",
            parse_mode="HTML",
        )

    group_id = cfg["group_id"]
    if not group_id:
        return await message.answer(
            "⚠️  <b>GROUP_ID</b> sozlanmagan.",
            parse_mode="HTML",
        )

    masul_name = message.from_user.full_name if message.from_user else "Noma'lum"
    start_time = now_dt()
    sid = storage.next_session_id()

    storage.reset_session()
    storage.active_session = {
        "id": sid,
        "start_time": start_time,
        "masul_id": uid,
        "masul_name": masul_name,
        "group_chat_id": group_id,
        "group_message_id": None,
        "status": "active",
    }
    storage.add_masul_as_participant(uid, masul_name)

    sent = await bot.send_message(
        group_id,
        group_live_card(now=start_time),
        reply_markup=group_live_keyboard(),
        parse_mode="HTML",
    )
    storage.active_session["group_message_id"] = sent.message_id

    if app_context.ticker:
        await app_context.ticker.start()

    await message.answer(
        f"✅  <b>Jarayon #{sid} boshlandi</b>\n"
        f"🕒  {fmt_hm(start_time)}\n\n"
        "Guruhda <b>LIVE</b> panel yuborildi.",
        parse_mode="HTML",
    )


router.message.register(cmd_start, Command("start"))
router.message.register(cmd_zones, Command("zones"))
router.message.register(cmd_id, Command("id"))
router.message.register(cmd_startmove, Command("startmove"))
