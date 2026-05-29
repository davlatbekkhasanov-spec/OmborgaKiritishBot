"""Klaviaturalar."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

import storage
from config import is_admin
from hub_test import BTN_HUB_TEST
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
    admin_row = [[KeyboardButton(text=BTN_HUB_TEST)]] if is_admin(user_id) else []
    if storage.has_user_session(user_id):
        keyboard = [
            [KeyboardButton(text=BTN_TRIP), KeyboardButton(text=BTN_FINISH)],
            [KeyboardButton(text=BTN_PICK_ZONE)],
        ]
        keyboard.extend(admin_row)
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            is_persistent=True,
        )

    keyboard = [[KeyboardButton(text=BTN_START_MOVE)]]
    keyboard.extend(admin_row)
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        is_persistent=True,
    )
