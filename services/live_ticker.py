"""Guruh kartasini LIVE yangilash."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from config import settings
import storage
from keyboards import group_live_keyboard
from ui import group_live_card

log = logging.getLogger(__name__)


class LiveTicker:
    def __init__(self, bot: Bot) -> None:
        self._bot = bot
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self.stop()
        self._task = asyncio.create_task(self._loop())

    def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None

    async def refresh(self) -> None:
        await self._edit()

    async def _loop(self) -> None:
        tick = settings()["tick_sec"]
        try:
            while storage.has_active_session():
                await self._edit()
                await asyncio.sleep(tick)
        except asyncio.CancelledError:
            pass

    async def _edit(self) -> None:
        sess = storage.active_session
        if not sess:
            return
        chat_id = sess.get("group_chat_id")
        msg_id = sess.get("group_message_id")
        if not chat_id or not msg_id:
            return
        try:
            await self._bot.edit_message_text(
                group_live_card(),
                chat_id=chat_id,
                message_id=msg_id,
                reply_markup=group_live_keyboard(),
                parse_mode="HTML",
            )
        except TelegramBadRequest as e:
            if "message is not modified" in str(e).lower():
                return
            log.warning("Live edit: %s", e)
        except Exception as e:
            log.warning("Live edit: %s", e)
