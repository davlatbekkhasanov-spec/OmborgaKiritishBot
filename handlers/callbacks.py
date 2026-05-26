"""Guruh — qatnashish va noto'g'ri zona bosish."""

from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

import app_context
from keyboards import CB_JOIN, CB_ZONE_PREFIX, worker_private_keyboard
import storage
from ui import private_worker_ready_card

router = Router(name="callbacks")
log = logging.getLogger(__name__)


async def _notify_worker_private(bot: Bot, user_id: int, name: str) -> None:
    try:
        await bot.send_message(
            user_id,
            private_worker_ready_card(
                name=name, bot_username=app_context.bot_username
            ),
            parse_mode="HTML",
            reply_markup=worker_private_keyboard(),
        )
    except TelegramForbiddenError:
        log.info("User %s botni /start qilmagan — shaxsiy xabar yuborilmadi", user_id)
    except Exception as e:
        log.warning("Shaxsiy xabar %s: %s", user_id, e)


async def _process_join(user_id: int, full_name: str, bot: Bot) -> tuple[bool, str]:
    ok, msg = storage.try_join(user_id, full_name)
    if ok:
        if app_context.ticker:
            await app_context.ticker.refresh()
        await _notify_worker_private(bot, user_id, full_name)
        msg = f"{msg}\n\nShaxsiy chatda /start bosing — tugmalar chiqadi."
    return ok, msg


@router.callback_query(F.data == CB_JOIN)
async def on_join_callback(callback: CallbackQuery, bot: Bot) -> None:
    user = callback.from_user
    if not user:
        return
    ok, msg = await _process_join(user.id, user.full_name or "Noma'lum", bot)
    await callback.answer(msg, show_alert=not ok)


@router.callback_query(
    F.data.startswith(CB_ZONE_PREFIX),
    F.message.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
)
async def on_zone_in_group(callback: CallbackQuery) -> None:
    await callback.answer(
        "Zonani shaxsiy chatda tanlang yoki QR skaner qiling.",
        show_alert=True,
    )


@router.message(Command("qatnashish"))
async def cmd_qatnashish(message: Message, bot: Bot) -> None:
    if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return await message.answer("Faqat guruhda.", parse_mode="HTML")
    user = message.from_user
    if not user:
        return
    ok, msg = await _process_join(user.id, user.full_name or "Noma'lum", bot)
    await message.answer(msg, parse_mode="HTML")
