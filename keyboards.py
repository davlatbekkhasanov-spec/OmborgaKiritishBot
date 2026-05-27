"""Klaviaturalar."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

import storage
from texts import BTN_FINISH, BTN_PICK_ZONE, BTN_START_MOVE, BTN_TRIP
from zones_config import zone_leg_meter

CB_ZONE_PREFIX = "ombor:zone:"


def _zone_button_label(z: dict) -> str:
    name = str(z.get("zone_name", ""))
    if len(name) > 20:
        name = name[:19] + "…"
    leg = zone_leg_meter(z)
    return f"{name} · {leg}m"


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


def private_keyboard_for(user_id: int) -> ReplyKeyboardMarkup:
    if storage.has_user_session(user_id):
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=BTN_TRIP), KeyboardButton(text=BTN_FINISH)],
                [KeyboardButton(text=BTN_PICK_ZONE)],
            ],
            resize_keyboard=True,
            is_persistent=True,
        )

    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_START_MOVE)]],
        resize_keyboard=True,
        is_persistent=True,
    )
