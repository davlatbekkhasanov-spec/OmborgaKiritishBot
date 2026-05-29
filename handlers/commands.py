"""Buyruqlar."""

from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

import app_context
from config import get_group_id, is_admin, settings
from hub_test import BTN_HUB_TEST
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
from zones_config import (
    TELEGRAM_ANDROID_PACKAGE,
    ZONES,
    bot_web_deep_link,
    zone_deep_link,
)
from ui import he, main_hint_card, zones_list_card

router = Router(name="commands")
log = logging.getLogger(__name__)


async def cmd_start(message: Message, command: CommandObject, bot: Bot) -> None:
    args = (command.args or "").strip().lower()
    uid = message.from_user.id if message.from_user else 0

    if args == "reys":
        if message.chat.type != ChatType.PRIVATE:
            return await message.answer(
                "📦  Reys uchun botga <b>shaxsiy</b> yozing yoki NFC ni shu yerda ishlating.",
                parse_mode="HTML",
            )
        from handlers.zone_pick import send_trip_started

        await send_trip_started(bot, message.chat.id, uid)
        await message.answer(
            "⌨️  Tugmalar:",
            reply_markup=private_keyboard_for(uid),
        )
        return

    zone = storage.parse_zone_payload(command.args)
    if zone:
        from handlers.qr import handle_zone_scan

        ok = await handle_zone_scan(message, bot, zone)
        if uid:
            await message.answer(
                "⌨️  Tugmalar:",
                reply_markup=private_keyboard_for(uid),
            )
        return

    user = message.from_user
    name = user.full_name if user else "Mehmon"
    uid = user.id if user else 0
    hint = main_hint_card(name=name, user_id=uid)
    if is_admin(uid):
        hint += f"\n\n<i>Admin: {BTN_HUB_TEST} yoki /test_hub</i>"
    await message.answer(
        hint,
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


async def cmd_nfcprint(message: Message) -> None:
    """NFC — Android: URL + Application record (AAR)."""
    bot_user = app_context.bot_username
    if not bot_user:
        return await message.answer("Bot username topilmadi.", parse_mode="HTML")

    reys_url = bot_web_deep_link(bot_user, "reys")
    pkg = TELEGRAM_ANDROID_PACKAGE
    lines = [
        "📲  <b>Android NFC — to'g'ri usul (2 ta yozuv)</b>\n",
        "<b>1.</b> NFC Tools → <b>Erase tag</b>\n",
        "<b>2.</b> + Создание сообщения NFC:\n",
        f"   • <b>URL</b> → <code>{reys_url}</code>\n",
        f"   • <b>Приложение</b> → <code>{pkg}</code>\n",
        "<b>3.</b> Продолжить → stikerga yozing\n",
        "<b>4.</b> Read bilan tekshiring — 2 ta record ko'rinsin\n",
        "━━━━━━━━━━━━━━━━━━━━\n",
        "<b>❌ Ishlamaydi:</b> faqat tg:// yoki faqat intent://\n",
        "<b>❌ «aka» ilovasini</b> o'chiring yoki o'chirib qo'ying\n",
        "\n<b>Zonalar:</b> /nfcprint_zonalar",
    ]
    await message.answer("\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)


async def cmd_nfcprint_zones(message: Message) -> None:
    bot_user = app_context.bot_username
    if not bot_user:
        return await message.answer("Bot username topilmadi.", parse_mode="HTML")
    lines = [
        "📲  <b>Zona NFC</b>\n",
        "<i>Har stiker: URL + Приложение org.telegram.messenger</i>\n",
    ]
    for code, z in ZONES.items():
        link = bot_web_deep_link(bot_user, f"zone_{code}")
        lines.append(f"\n<b>{he(z['zone_name'])}</b>\nURL: <code>{link}</code>")
    await message.answer("\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)


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
router.message.register(cmd_nfcprint, Command("nfcprint"))
router.message.register(cmd_nfcprint_zones, Command("nfcprint_zonalar"))
