"""Klaviaturalar."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from texts import BTN_FINISH, BTN_JOIN, BTN_START_MOVE, BTN_TRIP, BTN_ZONES_MENU

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
    """Shaxsiy chat — Boshlash, Yakunlash, Zonalar."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BTN_START_MOVE),
                KeyboardButton(text=BTN_FINISH),
            ],
            [KeyboardButton(text=BTN_ZONES_MENU)],
        ],
        resize_keyboard=True,
    )
