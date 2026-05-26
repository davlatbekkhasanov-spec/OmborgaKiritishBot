"""Guruh — zona tugmasi xato bosilganda."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.types import CallbackQuery

from keyboards import CB_ZONE_PREFIX

router = Router(name="callbacks")


@router.callback_query(
    F.data.startswith(CB_ZONE_PREFIX),
    F.message.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
)
async def on_zone_in_group(callback: CallbackQuery) -> None:
    await callback.answer(
        "Zonani botda shaxsiy chatda tanlang yoki QR skaner qiling.",
        show_alert=True,
    )
