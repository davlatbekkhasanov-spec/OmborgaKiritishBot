"""Mini App — kamera orqali QR skaner."""

from __future__ import annotations

import json
import logging

from aiogram import Bot, F, Router
from aiogram.types import Message

import app_context
from handlers.qr import handle_zone_scan
from qr_parse import parse_zone_from_text

router = Router(name="webapp_scan")
log = logging.getLogger(__name__)


@router.message(F.web_app_data)
async def on_qr_webapp(message: Message, bot: Bot) -> None:
    raw = message.web_app_data.data if message.web_app_data else ""
    zone = None
    try:
        payload = json.loads(raw)
        if isinstance(payload, dict):
            zone = parse_zone_from_text(str(payload.get("zone", "")))
    except json.JSONDecodeError:
        zone = parse_zone_from_text(raw)

    if not zone:
        zone = parse_zone_from_text(raw)

    if not zone:
        await message.answer(
            "⚠️  QR dan zona aniqlanmadi.\n"
            "Zona QR da <code>zone_OMBOR_A</code> bo'lishi kerak.",
            parse_mode="HTML",
        )
        return

    log.info("WebApp QR zone=%s user=%s", zone, message.from_user.id if message.from_user else 0)
    await handle_zone_scan(message, bot, zone)
