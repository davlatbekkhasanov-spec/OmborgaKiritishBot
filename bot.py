"""Omborga Kiritish Bot — premium LIVE panel (RAM)."""

from __future__ import annotations

import asyncio
import logging
import sys

from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import app_context
from config import settings, startup_warnings
from handlers import setup_routers
from services.group_check import GroupConfigError, verify_group_access
from hub_day_log import list_today_pushes
from services.live_ticker import LiveTicker
from yordamchi_push import push_to_yordamchi_hub, today_iso

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


async def main() -> None:
    cfg = settings()
    if not cfg["token"]:
        log.error("BOT_TOKEN topilmadi")
        sys.exit(1)

    for w in startup_warnings():
        log.warning(w)

    bot = Bot(
        token=cfg["token"],
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    if cfg["group_id"]:
        try:
            title = await verify_group_access(bot)
            log.info("Guruh OK: %s", title)
        except GroupConfigError as e:
            log.error("Guruh ulanishi: %s — /guruh yoki GROUP_ID ni tuzating", e)

    me = await bot.get_me()
    app_context.bot_username = (me.username or "").strip()
    app_context.ticker = LiveTicker(bot)

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(setup_routers())

    log.info(
        "✨ Bot ishga tushdi @%s | GROUP=%s | RAM",
        app_context.bot_username,
        cfg["group_id"],
    )

    try:
        day = today_iso()
        rows = list_today_pushes(day)
        sent = 0
        for tg_id, summary in rows:
            ok, _via = await push_to_yordamchi_hub(
                tg_id=tg_id,
                bot_key="omborga",
                summary=summary,
                day_iso=day,
            )
            if ok:
                sent += 1
        if rows:
            log.info("Omborga hub backfill: %s/%s for %s", sent, len(rows), day)
    except Exception:
        log.exception("omborga hub backfill xato")

    try:
        await dp.start_polling(bot)
    finally:
        if app_context.ticker:
            app_context.ticker.stop()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
