"""Guruh LIVE panelini avtomatik yangilash."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot

from config import settings
import storage
from services.group_panel import refresh_group_panel

log = logging.getLogger(__name__)


class LiveTicker:
    def __init__(self, bot: Bot) -> None:
        self._bot = bot
        self._task: asyncio.Task | None = None

    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> None:
        self.stop()
        self._task = asyncio.create_task(self._loop())

    def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None

    async def refresh(self) -> None:
        await refresh_group_panel(self._bot)

    async def _loop(self) -> None:
        tick = settings()["tick_sec"]
        try:
            while storage.any_active_users():
                await refresh_group_panel(self._bot)
                await asyncio.sleep(tick)
        except asyncio.CancelledError:
            pass
