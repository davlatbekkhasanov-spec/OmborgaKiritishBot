"""Klaviaturalar."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

import storage
from texts import BTN_FINISH, BTN_JOIN, BTN_PICK_ZONE, BTN_START_MOVE, BTN_TRIP

CB_JOIN = "ombor:join"
CB_ZONE_PREFIX = "ombor:zone:"


def group_live_keyboard() -> InlineKeyboardMarkup:
    """Guruhda faqat qatnashish."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_JOIN, callback_data=CB_JOIN)],
        ]
    )


def _zone_button_label(z: dict) -> str:
    name = str(z.get("zone_name", ""))
    if len(name) > 22:
        name = name[:21] + "…"
    ekv = z.get("effort_meter", z.get("distance_meter", 0))
    return f"{name} · {ekv}m"


def zone_inline_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for code, z in storage.ZONES.items():
        row.append(
            InlineKeyboardButton(
                text=_zone_button_label(z),
                callback_data=f"{CB_ZONE_PREFIX}{code}",
            )
        )
        if len(row) >= 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def worker_private_keyboard() -> ReplyKeyboardMarkup:
    """Ishchi — shaxsiy chat (joylashuv / WebApp yo'q)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_TRIP)],
            [KeyboardButton(text=BTN_PICK_ZONE)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def masul_private_keyboard() -> ReplyKeyboardMarkup:
    """Mas'ul — boshqaruv + o'zi ham reys qila oladi."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BTN_START_MOVE),
                KeyboardButton(text=BTN_FINISH),
            ],
            [
                KeyboardButton(text=BTN_TRIP),
                KeyboardButton(text=BTN_PICK_ZONE),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def private_keyboard_for(user_id: int) -> ReplyKeyboardMarkup:
    from config import is_admin

    if is_admin(user_id):
        return masul_private_keyboard()
    sess = storage.active_session
    if sess and int(sess.get("masul_id", 0)) == int(user_id):
        return masul_private_keyboard()
    return worker_private_keyboard()
