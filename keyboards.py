"""Klaviaturalar."""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from config import settings
from texts import BTN_FINISH, BTN_JOIN, BTN_QR_SCAN, BTN_START_MOVE, BTN_TRIP, BTN_ZONES_MENU

CB_JOIN = "ombor:join"
CB_TRIP = "ombor:trip"
CB_FINISH = "ombor:finish"


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


def private_main_keyboard() -> ReplyKeyboardMarkup:
    """Shaxsiy chat — skaner, boshlash, yakunlash."""
    rows: list[list[KeyboardButton]] = [
        [KeyboardButton(text=BTN_QR_SCAN, web_app=WebAppInfo(url=settings()["webapp_url"]))],
        [
            KeyboardButton(text=BTN_START_MOVE),
            KeyboardButton(text=BTN_FINISH),
        ],
        [KeyboardButton(text=BTN_ZONES_MENU)],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
