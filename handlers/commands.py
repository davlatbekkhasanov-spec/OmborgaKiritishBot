"""Buyruqlar."""

from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

import app_context
from config import get_group_id, is_admin, settings
import storage
from keyboards import group_live_keyboard, private_main_keyboard
from services.group_check import (
    GroupConfigError,
    group_fix_message,
    is_group_chat,
    parse_group_id_hint,
    resolve_target_group_id,
    verify_group_access,
)
from handlers.zone_pick import send_zone_picker
from texts import BTN_PICK_ZONE, BTN_START_MOVE, BTN_ZONES_MENU
from zones_config import ZONES, zone_deep_link
from ui import group_live_card, he, welcome_card, worker_hint_card, zones_list_card
from keyboards import zone_inline_keyboard
from time_util import fmt_hm, now_dt

router = Router(name="commands")
log = logging.getLogger(__name__)


async def cmd_start(message: Message, command: CommandObject, bot: Bot) -> None:
    zone = storage.parse_zone_payload(command.args)
    if zone:
        from handlers.qr import handle_zone_scan

        await handle_zone_scan(message, bot, zone)
        return

    user = message.from_user
    name = user.full_name if user else "Mehmon"
    uid = user.id if user else 0
    kb = private_main_keyboard()
    if is_admin(uid):
        text = welcome_card(is_masul=True, name=name)
    else:
        text = worker_hint_card(name=name, session_active=storage.has_active_session())
        if settings()["admin_ids"]:
            text += (
                f"\n\n<i>Mas'ul: Railway → "
                f"<code>ADMIN_IDS={uid}</code></i>"
            )
    await message.answer(text, parse_mode="HTML", reply_markup=kb)


async def cmd_zones(message: Message, bot: Bot) -> None:
    uid = message.from_user.id if message.from_user else 0
    if uid in storage.active_trips:
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
            "\n\n✅  Shu raqamni Railway → <code>GROUP_ID</code> ga yozing.\n"
            "<i>Bot guruhda bo'lishi shart.</i>"
        )
    await message.answer(
        f"📌  <b>Chat ID</b>\n<code>{message.chat.id}</code>\n\n"
        f"👤  <b>Sizning ID</b>\n<code>{uid}</code>{extra}",
        parse_mode="HTML",
    )


async def cmd_guruh(message: Message, bot: Bot) -> None:
    """GROUP_ID tekshiruvi (shaxsiy chat)."""
    uid = message.from_user.id if message.from_user else 0
    if settings()["admin_ids"] and not is_admin(uid):
        return await message.answer("⚠️  Faqat mas'ul/admin.", parse_mode="HTML")
    if is_group_chat(message):
        return await message.answer(
            "Bu buyruqni <b>shaxsiy chatda</b> yuboring.\n"
            "Guruhda esa to'g'ridan-to'g'ri <b>🚀 Boshlash</b> bosing.",
            parse_mode="HTML",
        )
    try:
        title = await verify_group_access(bot)
        cfg = settings()["group_id"]
        resolved = get_group_id()
        fix = ""
        if resolved and cfg and resolved != cfg:
            fix = f"\n\n💡  Railway yangilang:\n<code>GROUP_ID={resolved}</code>"
        await message.answer(
            f"✅  <b>Guruh topildi</b>\n\n"
            f"📛  <b>{title}</b>\n\n"
            f"{parse_group_id_hint()}{fix}",
            parse_mode="HTML",
        )
    except GroupConfigError as e:
        await message.answer(group_fix_message(detail=str(e)), parse_mode="HTML")


async def cmd_startmove(message: Message, bot: Bot) -> None:
    uid = message.from_user.id if message.from_user else 0
    cfg = settings()

    if cfg["admin_ids"] and not is_admin(uid):
        return await message.answer(
            "⛔  Faqat <b>mas'ul/admin</b> jarayonni boshlaydi.\n"
            f"Sizning ID: <code>{uid}</code>\n"
            "Railway → <b>ADMIN_IDS</b>",
            parse_mode="HTML",
        )

    if storage.has_active_session():
        return await message.answer(
            "⚠️  Aktiv jarayon bor. Avval <b>Yakunlash</b>.",
            parse_mode="HTML",
        )

    group_id, err = await resolve_target_group_id(bot, message)
    if err or not group_id:
        return await message.answer(err or group_fix_message(), parse_mode="HTML")

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

    try:
        sent = await bot.send_message(
            group_id,
            group_live_card(now=start_time),
            reply_markup=group_live_keyboard(),
            parse_mode="HTML",
        )
    except Exception as e:
        storage.reset_session()
        log.exception("Guruhga yuborish xatosi: %s", e)
        return await message.answer(
            group_fix_message(detail=str(e)[:200]),
            parse_mode="HTML",
        )

    storage.active_session["group_message_id"] = sent.message_id

    if app_context.ticker:
        await app_context.ticker.start()

    where = "shu guruhda" if is_group_chat(message) else "ishchi guruhda"
    await message.answer(
        f"✅  <b>Jarayon #{sid} boshlandi</b>\n"
        f"🕒  {fmt_hm(start_time)}\n\n"
        f"📣  LIVE panel <b>{where}</b> yuborildi.\n"
        f"🆔  Guruh ID: <code>{group_id}</code>",
        parse_mode="HTML",
        reply_markup=private_main_keyboard() if not is_group_chat(message) else None,
    )


async def cmd_zones_menu(message: Message, bot: Bot) -> None:
    await cmd_zones(message, bot)


async def cmd_pick_zone(message: Message, bot: Bot) -> None:
    uid = message.from_user.id if message.from_user else 0
    await send_zone_picker(bot, message.chat.id, uid)


async def cmd_qrprint(message: Message) -> None:
    """Mas'ul: chop etish uchun havolalar + yo'riqnoma."""
    uid = message.from_user.id if message.from_user else 0
    if settings()["admin_ids"] and not is_admin(uid):
        return await message.answer("⚠️  Faqat mas'ul/admin.", parse_mode="HTML")

    bot_user = app_context.bot_username
    if not bot_user:
        return await message.answer(
            "Bot username topilmadi. Redeploy qiling.",
            parse_mode="HTML",
        )

    lines = [
        "🖨  <b>QR chop etish</b>\n",
        "Kompyuterda bir marta:\n",
        "<code>pip install qrcode[pil] pillow</code>\n",
        f"<code>python scripts/generate_zone_qr.py --bot {bot_user}</code>\n",
        "Papka: <b>qr_print/</b> — PNG + chop_etish.html\n\n",
        "━━━━ Havolalar (tezkor) ━━━━\n",
    ]
    for code, z in ZONES.items():
        url = zone_deep_link(bot_user, code)
        lines.append(
            f"\n<b>{he(z['zone_name'])}</b>\n"
            f"gor {z['horizontal_meter']}m · ekv {z['effort_meter']}m\n"
            f"<code>{url}</code>"
        )

    await message.answer("\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)


router.message.register(cmd_start, Command("start"))
router.message.register(cmd_zones, Command("zones"))
router.message.register(cmd_guruh, Command("guruh"))
router.message.register(cmd_zones_menu, F.text == BTN_ZONES_MENU)
router.message.register(cmd_pick_zone, F.text == BTN_PICK_ZONE)
router.message.register(cmd_id, Command("id"))
router.message.register(cmd_startmove, Command("startmove"))
router.message.register(cmd_startmove, F.text == BTN_START_MOVE)
router.message.register(cmd_qrprint, Command("qrprint"))
