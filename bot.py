"""Omborga Kiritish Bot — to'liq scenariy (RAM)."""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import is_admin, settings, startup_warnings
import storage
from stats import build_final_report
from states import FinishStates
from time_util import fmt_elapsed, fmt_hm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

CB_JOIN = "join_move"
CB_TRIP = "trip_start"
CB_FINISH = "finish_move"

_ticker_task: asyncio.Task | None = None
_bot_username: str = ""


def group_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Qatnashish", callback_data=CB_JOIN)],
            [
                InlineKeyboardButton(text="📦 Reys oldim", callback_data=CB_TRIP),
                InlineKeyboardButton(text="🏁 Yakunlash", callback_data=CB_FINISH),
            ],
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
        for i, p in enumerate(
            sorted(storage.participants.values(), key=lambda x: x["join_time"]), 1
        ):
            ws_count = sum(1 for t in storage.trips if t["user_id"] == p["user_id"])
            trip_mark = f" · {ws_count} reys" if ws_count else ""
            lines.append(
                f"{i}. {p['full_name']} — {fmt_elapsed(p['join_time'], now)}{trip_mark}"
            )

    open_count = len(storage.active_trips)
    if open_count:
        lines.append(f"\n🔄 Ochiq reyslar: {open_count}")

    return "\n".join(lines)


def zone_qr_hint() -> str:
    if not _bot_username:
        return "QR: /start zone_OMBOR_A (bot username sozlanmagan)"
    lines = ["📍 QR zonalar (namuna):"]
    for code in storage.ZONES:
        lines.append(
            f"https://t.me/{_bot_username}?start=zone_{code}"
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
            reply_markup=group_keyboard(),
        )
    except Exception as e:
        if "message is not modified" in str(e).lower():
            return
        log.warning("Guruh yangilash: %s", e)


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


async def on_start(message: Message, command: CommandObject, bot: Bot) -> None:
    zone = storage.parse_zone_payload(command.args)
    if zone:
        uid = message.from_user.id if message.from_user else 0
        ok, msg = storage.try_complete_trip(uid, zone)
        await message.answer(msg)
        if ok:
            await edit_group_live(bot)
        return

    await message.answer(
        "📦 <b>Omborga Kiritish Bot</b>\n\n"
        "/startmove — jarayonni boshlash (mas'ul)\n"
        "/id — chat ID\n"
        "/zones — QR zonalar ro'yxati\n\n"
        "Ishchi: guruhda qatnashing → Reys oldim → zonada QR skaner.",
        parse_mode="HTML",
    )


async def on_zones(message: Message) -> None:
    await message.answer(zone_qr_hint())


async def on_id(message: Message) -> None:
    await message.answer(
        f"📌 Chat ID:\n<code>{message.chat.id}</code>", parse_mode="HTML"
    )


async def on_startmove(message: Message, bot: Bot) -> None:
    uid = message.from_user.id if message.from_user else 0
    cfg = settings()

    if cfg["admin_ids"] and not is_admin(uid):
        return await message.answer("⛔ Faqat mas'ul/admin /startmove yubora oladi.")

    if storage.has_active_session():
        return await message.answer("⚠️ Aktiv jarayon bor. Avval yakunlang.")

    group_id = cfg["group_id"]
    if not group_id:
        return await message.answer("⚠️ GROUP_ID sozlanmagan.")

    masul_name = message.from_user.full_name if message.from_user else "Noma'lum"
    start_time = datetime.now()

    storage.reset_session()
    storage.active_session = {
        "start_time": start_time,
        "masul_id": uid,
        "masul_name": masul_name,
        "group_chat_id": group_id,
        "group_message_id": None,
        "status": "active",
    }
    storage.add_masul_as_participant(uid, masul_name)

    sent = await bot.send_message(
        group_id,
        build_group_text(start_time),
        reply_markup=group_keyboard(),
    )
    storage.active_session["group_message_id"] = sent.message_id
    start_ticker(bot)

    await message.answer(
        f"✅ Jarayon boshlandi.\n🕒 {fmt_hm(start_time)}\n"
        f"Guruhga xabar yuborildi.\n\n{zone_qr_hint()}"
    )


async def on_join(callback: CallbackQuery, bot: Bot) -> None:
    user = callback.from_user
    if not user:
        return
    ok, msg = storage.try_join(user.id, user.full_name or "Noma'lum")
    await callback.answer(msg, show_alert=not ok)
    if ok:
        await edit_group_live(bot)


async def on_trip(callback: CallbackQuery, bot: Bot) -> None:
    user = callback.from_user
    if not user:
        return
    ok, msg = storage.try_start_trip(user.id)
    await callback.answer(msg, show_alert=not ok)
    if ok:
        await edit_group_live(bot)
        try:
            await bot.send_message(
                user.id,
                f"{msg}\n\n{zone_qr_hint()}",
            )
        except Exception:
            pass


async def on_finish_click(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    user = callback.from_user
    if not user:
        return
    if not storage.has_active_session():
        await callback.answer("Jarayon yo'q.", show_alert=True)
        return
    if not storage.can_manage(user.id):
        await callback.answer("Faqat mas'ul/admin yakunlaydi.", show_alert=True)
        return
    if storage.active_trips:
        await callback.answer(
            "Ochiq reyslar bor. Avval QR skaner qiling yoki kuting.",
            show_alert=True,
        )
        return

    storage.active_session["status"] = "finishing"
    stop_ticker()
    await callback.answer()

    await state.set_state(FinishStates.waiting_ombor_photo)
    try:
        await bot.send_message(
            user.id,
            "🏁 <b>Yakunlash</b>\n\n"
            "1/2 — Omborga olib kirilgan yuklar <b>rasmini</b> yuboring.",
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            "Shaxsiy chatda botni /start bosing, keyin qayta «Yakunlash»."
        )


async def on_finish_ombor_photo(message: Message, state: FSMContext) -> None:
    if not message.photo:
        return await message.answer("Rasm yuboring (foto).")
    storage.photos["ombor"] = message.photo[-1].file_id
    await state.set_state(FinishStates.waiting_bosh_joy_photo)
    await message.answer(
        "2/2 — Tashqaridagi joy bo'shagan <b>rasmini</b> yuboring.",
        parse_mode="HTML",
    )


async def on_finish_bosh_joy_photo(
    message: Message, state: FSMContext, bot: Bot
) -> None:
    if not message.photo:
        return await message.answer("Rasm yuboring (foto).")

    storage.photos["bosh_joy"] = message.photo[-1].file_id
    await state.clear()

    report = build_final_report()
    sess = storage.active_session
    group_id = sess["group_chat_id"] if sess else settings()["group_id"]

    if group_id:
        await bot.send_message(group_id, report)
        for key, fid in storage.photos.items():
            cap = {"ombor": "Ombordagi", "bosh_joy": "Bo'shagan joy", "boshlangich": "Boshlang'ich"}.get(
                key, key
            )
            await bot.send_photo(group_id, fid, caption=f"📸 {cap}")

    await message.answer(f"✅ Yakunlandi.\n\n{report}")
    storage.reset_session()


async def on_cancel_finish(message: Message, state: FSMContext, bot: Bot) -> None:
    await state.clear()
    if storage.is_finishing() and storage.active_session:
        storage.active_session["status"] = "active"
        start_ticker(bot)
        await message.answer("Yakunlash bekor qilindi. Jarayon davom etmoqda.")
    else:
        await message.answer("Bekor qilindi.")


def setup_dp() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.register(on_start, Command("start"))
    dp.message.register(on_zones, Command("zones"))
    dp.message.register(on_id, Command("id"))
    dp.message.register(on_startmove, Command("startmove"))
    dp.message.register(on_cancel_finish, Command("cancel"))
    dp.message.register(
        on_finish_ombor_photo,
        StateFilter(FinishStates.waiting_ombor_photo),
        F.photo,
    )
    dp.message.register(
        on_finish_bosh_joy_photo,
        StateFilter(FinishStates.waiting_bosh_joy_photo),
        F.photo,
    )
    dp.callback_query.register(on_join, F.data == CB_JOIN)
    dp.callback_query.register(on_trip, F.data == CB_TRIP)
    dp.callback_query.register(on_finish_click, F.data == CB_FINISH)
    return dp


async def main() -> None:
    global _bot_username
    cfg = settings()
    if not cfg["token"]:
        log.error("BOT_TOKEN topilmadi")
        sys.exit(1)

    for w in startup_warnings():
        log.warning(w)

    bot = Bot(token=cfg["token"])
    me = await bot.get_me()
    _bot_username = (me.username or "").strip()

    dp = setup_dp()
    log.info(
        "Bot ishga tushdi (@%s, GROUP_ID=%s, RAM)",
        _bot_username,
        cfg["group_id"],
    )

    try:
        await dp.start_polling(bot)
    finally:
        stop_ticker()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
