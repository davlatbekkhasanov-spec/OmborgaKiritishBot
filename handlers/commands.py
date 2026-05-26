"""Buyruqlar."""

from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

import app_context
from config import get_group_id, settings
import storage
from keyboards import private_keyboard_for, zone_inline_keyboard
from services.group_check import (
    GroupConfigError,
    group_fix_message,
    is_group_chat,
    parse_group_id_hint,
    verify_group_access,
)
from handlers.zone_pick import send_zone_picker
from texts import BTN_ZONES_MENU
from zones_config import ZONES, zone_deep_link
from ui import he, main_hint_card, zones_list_card

router = Router(name="commands")
log = logging.getLogger(__name__)


async def cmd_start(message: Message, command: CommandObject, bot: Bot) -> None:
    zone = storage.parse_zone_payload(command.args)
    if zone:
        from handlers.qr import handle_zone_scan

        ok = await handle_zone_scan(message, bot, zone)
        uid = message.from_user.id if message.from_user else 0
        if uid:
            await message.answer(
                "⌨️  Tugmalar:",
                reply_markup=private_keyboard_for(uid),
            )
        return

    user = message.from_user
    name = user.full_name if user else "Mehmon"
    uid = user.id if user else 0
    await message.answer(
        main_hint_card(name=name, user_id=uid),
        parse_mode="HTML",
        reply_markup=private_keyboard_for(uid),
    )


async def cmd_zones(message: Message, bot: Bot) -> None:
    if message.chat.type != ChatType.PRIVATE:
        return await message.answer(
            "📦  Zonalar uchun botga shaxsiy yozing.",
            parse_mode="HTML",
        )
    uid = message.from_user.id if message.from_user else 0
    if storage.user_has_open_trip(uid):
        await send_zone_picker(bot, message.chat.id, uid)
        return
    await message.answer(
        zones_list_card(bot_username=app_context.bot_username),
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=zone_inline_keyboard(),
    )


async def cmd_id(message: Message) -> None:
    uid = message.from_user.id if message.from_user else "—"
    extra = ""
    if is_group_chat(message):
        extra = (
            "\n\n✅  Railway → <code>GROUP_ID</code>\n"
            "<i>Bot guruhda bo'lishi shart.</i>"
        )
    await message.answer(
        f"📌  <b>Chat ID</b>\n<code>{message.chat.id}</code>\n\n"
        f"👤  <b>Sizning ID</b>\n<code>{uid}</code>{extra}",
        parse_mode="HTML",
    )


async def cmd_guruh(message: Message, bot: Bot) -> None:
    if is_group_chat(message):
        return await message.answer(
            "Bu buyruqni <b>shaxsiy chatda</b> yuboring.",
            parse_mode="HTML",
        )
    try:
        title = await verify_group_access(bot)
        cfg = settings()["group_id"]
        resolved = get_group_id()
        fix = ""
        if resolved and cfg and resolved != cfg:
            fix = f"\n\n💡  <code>GROUP_ID={resolved}</code>"
        await message.answer(
            f"✅  <b>Guruh topildi</b>\n\n📛  <b>{title}</b>\n\n"
            f"{parse_group_id_hint()}{fix}",
            parse_mode="HTML",
        )
    except GroupConfigError as e:
        await message.answer(group_fix_message(detail=str(e)), parse_mode="HTML")


async def cmd_zones_menu(message: Message, bot: Bot) -> None:
    await cmd_zones(message, bot)


async def cmd_qrprint(message: Message) -> None:
    bot_user = app_context.bot_username
    if not bot_user:
        return await message.answer("Bot username topilmadi.", parse_mode="HTML")
    lines = [
        "🖨  <b>QR chop etish</b>\n",
        f"<code>python scripts/generate_zone_qr.py --bot {bot_user}</code>\n\n",
    ]
    for code, z in ZONES.items():
        lines.append(
            f"\n<b>{he(z['zone_name'])}</b>\n<code>{zone_deep_link(bot_user, code)}</code>"
        )
    await message.answer("\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)


router.message.register(cmd_start, Command("start"))
router.message.register(cmd_zones, Command("zones"))
router.message.register(cmd_guruh, Command("guruh"))
router.message.register(cmd_zones_menu, F.text == BTN_ZONES_MENU)
router.message.register(cmd_id, Command("id"))
router.message.register(cmd_qrprint, Command("qrprint"))
