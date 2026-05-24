"""Ilova konteksti — ticker va bot username."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.live_ticker import LiveTicker

ticker: LiveTicker | None = None
bot_username: str = ""
