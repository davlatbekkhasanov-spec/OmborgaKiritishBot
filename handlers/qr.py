"""QR havola / matn — reysni yopish."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.types import Message

import storage
from qr_parse import parse_zone_from_text
from services.group_panel import notify_session_change
from texts import BTN_START_MOVE
from ui import he, trip_complete_card

router = Router(name="qr")


async def complete_zone_for_user(
    bot: Bot,
    chat_id: int,
    user_id: int,
    full_name: str,
    zone_code: str,
    *,
    auto_start_trip: bool = True,
) -> bool:
    if not storage.has_user_session(user_id):
        await bot.send_message(
            chat_id,
            f"⚠️  Avval <b>{he(BTN_START_MOVE)}</b> — yuk rasmini yuboring.",
            parse_mode="HTML",
        )
        return False

    if not storage.user_has_open_trip(user_id) and auto_start_trip:
        ok_start, start_msg = storage.try_start_trip(user_id)
        if not ok_start:
            await bot.send_message(chat_id, f"⚠️  {he(start_msg)}", parse_mode="HTML")
            return False

    ok, result = storage.try_complete_trip(user_id, zone_code)
    if not ok:
        hint = ""
        if "Ochiq reys" in str(result):
            hint = "\n\n👉  <b>📦 Reys oldim</b> bosing."
        await bot.send_message(chat_id, f"⚠️  {he(result)}{hint}", parse_mode="HTML")
        return False

    record = result
    await bot.send_message(
        chat_id,
        trip_complete_card(
            zone_name=record["zone_name"],
            distance_meter=record["distance_meter"],
            horizontal_meter=record.get("horizontal_meter"),
            effort_meter=record.get("effort_meter"),
            duration_sec=record["duration_sec"],
            worker_name=full_name,
        ),
        parse_mode="HTML",
    )
    await notify_session_change(bot)
    return True


def _user_from_message(message: Message) -> tuple[int, str] | None:
    user = message.from_user
    if not user or user.is_bot:
        return None
    return user.id, user.full_name or "Noma'lum"


async def handle_zone_scan(message: Message, bot: Bot, zone_code: str) -> bool:
    actor = _user_from_message(message)
    if not actor:
        return False
    uid, name = actor
    return await complete_zone_for_user(
        bot, message.chat.id, uid, name, zone_code
    )


@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.text.regexp(r"(?i)(?:start=)?zone_[a-z0-9_]+|t\.me/\w+\?start=zone_"),
)
async def on_qr_text_paste(message: Message, bot: Bot) -> None:
    zone = parse_zone_from_text(message.text or "")
    if zone:
        await handle_zone_scan(message, bot, zone)
