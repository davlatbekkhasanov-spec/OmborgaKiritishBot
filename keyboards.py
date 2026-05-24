"""Klaviaturalar."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

import storage
from texts import BTN_FINISH, BTN_JOIN, BTN_PICK_ZONE, BTN_START_MOVE, BTN_TRIP, BTN_ZONES_MENU

CB_JOIN = "ombor:join"
CB_TRIP = "ombor:trip"
CB_FINISH = "ombor:finish"
CB_ZONE_PREFIX = "ombor:zone:"


def group_live_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_JOIN, callback_data=CB_JOIN)],
            [
                InlineKeyboardButton(text=BTN_TRIP, callback_data=CB_TRIP),
                InlineKeyboardButton(text=BTN_FINISH, callback_data=CB_FINISH),
            ],
        ]
    )


def zone_inline_keyboard() -> InlineKeyboardMarkup:
    """Bir bosish — zona tanlash (Mini App siz)."""
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for code, z in storage.ZONES.items():
        row.append(
            InlineKeyboardButton(
                text=f"📍 {z['zone_name']} · {z['distance_meter']}m",
                callback_data=f"{CB_ZONE_PREFIX}{code}",
            )
        )
        if len(row) >= 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def private_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_PICK_ZONE)],
            [
                KeyboardButton(text=BTN_START_MOVE),
                KeyboardButton(text=BTN_FINISH),
            ],
            [KeyboardButton(text=BTN_ZONES_MENU)],
        ],
        resize_keyboard=True,
    )
