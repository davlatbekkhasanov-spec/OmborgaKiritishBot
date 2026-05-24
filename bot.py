"""Omborga Kiritish Bot — 1-bosqich (RAM)."""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import is_admin, settings, startup_warnings
import storage
from time_util import fmt_elapsed, fmt_hm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

CB_JOIN = "join_move"

_ticker_task: asyncio.Task | None = None


def join_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Qatnashish", callback_data=CB_JOIN)]
        ]
    )


def build_group_text(now: datetime | None = None) -> str:
    now = now or datetime.now()
    sess = storage.active_session
    if not sess:
        return "📦 Sessiya yo'q"

    lines = [
        "📦 OMBORGA KIRITISH BOSHLANDI",
        "",
        f"🕒 Boshlanish: {fmt_hm(sess['start_time'])}",
        f"👤 Mas'ul: {sess['masul_name']}",
        "",
        "👷 Qatnashuvchilar:",
    ]

    if not storage.participants:
        lines.append("Hozircha yo'q")
    else:
        ordered = sorted(
            storage.participants.values(),
            key=lambda p: p["join_time"],
        )
        for i, p in enumerate(ordered, 1):
            lines.append(
                f"{i}. {p['full_name']} — {fmt_elapsed(p['join_time'], now)}"
            )

    return "\n".join(lines)


async def edit_group_live(bot: Bot) -> None:
    sess = storage.active_session
    if not sess:
        return
    chat_id = sess.get("group_chat_id")
    msg_id = sess.get("group_message_id")
    if not chat_id or not msg_id:
        return
    try:
        await bot.edit_message_text(
            build_group_text(),
            chat_id=chat_id,
            message_id=msg_id,
            reply_markup=join_keyboard(),
        )
    except Exception as e:
        err = str(e).lower()
        if "message is not modified" in err:
            return
        log.warning("Guruh xabarini yangilash: %s", e)


async def ticker_loop(bot: Bot) -> None:
    tick = settings()["tick_sec"]
    while storage.has_active_session():
        await edit_group_live(bot)
        await asyncio.sleep(tick)


def start_ticker(bot: Bot) -> None:
    global _ticker_task
    stop_ticker()
    _ticker_task = asyncio.create_task(ticker_loop(bot))


def stop_ticker() -> None:
    global _ticker_task
    if _ticker_task and not _ticker_task.done():
        _ticker_task.cancel()
    _ticker_task = None


async def on_start(message: Message) -> None:
    await message.answer(
        "📦 <b>Omborga Kiritish Bot</b> ishlayapti\n\n"
        "/startmove — omborga kiritishni boshlash\n"
        "/id — chat ID",
        parse_mode="HTML",
    )


async def on_id(message: Message) -> None:
    await message.answer(f"📌 Chat ID:\n<code>{message.chat.id}</code>", parse_mode="HTML")


async def on_startmove(message: Message, bot: Bot) -> None:
    from datetime import datetime

    uid = message.from_user.id if message.from_user else 0
    cfg = settings()

    if cfg["admin_ids"] and not is_admin(uid):
        return await message.answer("⛔ Faqat mas'ul/admin /startmove yubora oladi.")

    if storage.has_active_session():
        return await message.answer(
            "⚠️ Aktiv jarayon bor. Avval yakunlang yoki botni qayta ishga tushiring."
        )

    group_id = cfg["group_id"]
    if not group_id:
        return await message.answer(
            "⚠️ GROUP_ID sozlanmagan.\n"
            "Railway Variables ga GROUP_ID qo'shing yoki guruhda /id bilan ID oling."
        )

    masul_name = (
        message.from_user.full_name if message.from_user else "Noma'lum"
    )
    start_time = datetime.now()

    storage.active_session = {
        "start_time": start_time,
        "masul_id": uid,
        "masul_name": masul_name,
        "group_chat_id": group_id,
        "group_message_id": None,
    }
    storage.participants.clear()
    storage.trips.clear()

    sent = await bot.send_message(
        group_id,
        build_group_text(start_time),
        reply_markup=join_keyboard(),
    )
    storage.active_session["group_message_id"] = sent.message_id

    start_ticker(bot)

    await message.answer(
        f"✅ Jarayon boshlandi.\n"
        f"🕒 {fmt_hm(start_time)}\n"
        f"Guruhga xabar yuborildi.",
    )


async def on_join(callback: CallbackQuery, bot: Bot) -> None:
    if callback.data != CB_JOIN:
        return

    if not storage.has_active_session():
        await callback.answer("Jarayon aktiv emas.", show_alert=True)
        return

    user = callback.from_user
    if not user:
        await callback.answer("Xato.", show_alert=True)
        return

    from datetime import datetime

    if user.id in storage.participants:
        await callback.answer("Siz allaqachon ro'yxatdasiz.", show_alert=True)
        return

    storage.participants[user.id] = {
        "user_id": user.id,
        "full_name": user.full_name or "Noma'lum",
        "join_time": datetime.now(),
    }

    await edit_group_live(bot)
    await callback.answer("Siz qatnashdingiz ✅")


def setup_dp() -> Dispatcher:
    dp = Dispatcher()
    dp.message.register(on_start, Command("start"))
    dp.message.register(on_id, Command("id"))
    dp.message.register(on_startmove, Command("startmove"))
    dp.callback_query.register(on_join, F.data == CB_JOIN)
    return dp


async def main() -> None:
    cfg = settings()
    if not cfg["token"]:
        log.error("BOT_TOKEN topilmadi — .env yoki Railway Variables")
        sys.exit(1)

    for w in startup_warnings():
        log.warning(w)

    bot = Bot(token=cfg["token"])
    dp = setup_dp()

    log.info("Bot ishga tushdi (GROUP_ID=%s, RAM storage)", cfg["group_id"])
    try:
        await dp.start_polling(bot)
    finally:
        stop_ticker()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
