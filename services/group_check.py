"""Guruhga yuborish — ID tekshiruv va -100 tuzatish."""

from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import Message

from config import get_group_id, set_resolved_group_id, settings

log = logging.getLogger(__name__)


class GroupConfigError(Exception):
    pass


def supergroup_id_candidate(group_id: int) -> int | None:
    s = str(group_id)
    if s.startswith("-") and not s.startswith("-100"):
        return int("-100" + s[1:])
    return None


def group_id_candidates(group_id: int) -> list[int]:
    out = [group_id]
    alt = supergroup_id_candidate(group_id)
    if alt is not None and alt not in out:
        out.append(alt)
    return out


def is_group_chat(message: Message) -> bool:
    return message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP)


def parse_group_id_hint() -> str:
    gid = settings()["group_id"]
    if gid is None:
        return (
            "Railway da <code>GROUP_ID</code> yo'q.\n"
            "Yoki <b>ishchi guruhda</b> «Boshlash» bosing."
        )
    lines = [f"Hozirgi <code>GROUP_ID={gid}</code>"]
    alt = supergroup_id_candidate(gid)
    if alt:
        lines.append(f"Sinab ko'ring: <code>GROUP_ID={alt}</code>")
    resolved = get_group_id()
    if resolved and resolved != gid:
        lines.append(f"Ishlayotgan ID: <code>{resolved}</code>")
    return "\n".join(lines)


def group_fix_message(*, detail: str = "") -> str:
    extra = f"\n\n<i>{detail}</i>" if detail else ""
    return (
        "⚠️  <b>Guruhga yuborib bo'lmadi</b>\n\n"
        "<b>Sabablar:</b>\n"
        "• <code>GROUP_ID</code> noto'g'ri\n"
        "• Bot guruhda yo'q\n"
        "• Bot admin emas\n\n"
        "<b>Tuzatish:</b>\n"
        "1️⃣ Botni <b>ishchi guruhga</b> qo'shing\n"
        "2️⃣ Guruhda <code>/id</code> — ID ni oling\n"
        "3️⃣ Railway → <code>GROUP_ID=-100...</code>\n"
        "4️⃣ <b>Redeploy</b>\n\n"
        "Yoki to'g'ridan-to'g'ri <b>guruhda</b> «🚀 Boshlash» bosing.\n\n"
        f"{parse_group_id_hint()}{extra}"
    )


async def verify_group_access(bot: Bot) -> str:
    configured = settings()["group_id"]
    if not configured:
        raise GroupConfigError("GROUP_ID sozlanmagan")

    last_err: Exception | None = None
    for chat_id in group_id_candidates(configured):
        try:
            chat = await bot.get_chat(chat_id)
            set_resolved_group_id(chat_id)
            if chat_id != configured:
                log.info("GROUP_ID %s → ishlaydigan ID %s", configured, chat_id)
            return chat.title or chat.full_name or str(chat_id)
        except TelegramBadRequest as e:
            last_err = e
            if "chat not found" not in str(e).lower():
                raise GroupConfigError(str(e)) from e
        except TelegramForbiddenError as e:
            raise GroupConfigError("Bot guruhda emas yoki bloklangan") from e

    raise GroupConfigError("chat not found") from last_err


async def resolve_target_group_id(bot: Bot, message: Message) -> tuple[int | None, str | None]:
    """
    Guruh chatidan — shu chat ID.
    Shaxsiy chatdan — GROUP_ID (tekshirilgan).
    """
    if is_group_chat(message):
        cid = message.chat.id
        set_resolved_group_id(cid)
        return cid, None

    configured = settings()["group_id"]
    if not configured:
        return None, group_fix_message(detail="GROUP_ID o'rnatilmagan")

    try:
        await verify_group_access(bot)
    except GroupConfigError as e:
        return None, group_fix_message(detail=str(e))

    return get_group_id(), None
