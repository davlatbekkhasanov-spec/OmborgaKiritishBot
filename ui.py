"""Premium Telegram HTML kartalar."""

from __future__ import annotations

import html as html_lib
from datetime import datetime
from typing import Any

import storage
from stats import SessionMetrics, ranked_workers, session_metrics, worker_stats
from texts import BRAND, BTN_JOIN, BTN_TRIP
from time_util import (
    display_now,
    ensure_aware,
    fmt_distance_m,
    fmt_duration,
    fmt_duration_short,
    fmt_elapsed,
    fmt_hm,
    now_dt,
)

_live_i = 0


def he(text: object) -> str:
    return html_lib.escape(str(text or ""))


def sep(char: str = "─", width: int = 26) -> str:
    return char * width


def banner(title: str, *, icon: str = "📦", width: int = 26) -> str:
    line = sep("═", width)
    return f"{line}\n{icon}  <b>{he(title)}</b>\n{line}"


def glow_bar(pct: int, width: int = 14) -> str:
    pct = max(0, min(100, int(pct)))
    filled = min(width, int(round(width * pct / 100)))
    return "▰" * filled + "▱" * (width - filled)


def rank_badge(i: int) -> str:
    if i == 1:
        return "🥇"
    if i == 2:
        return "🥈"
    if i == 3:
        return "🥉"
    return f"#{i:02d}"


def live_pulse() -> str:
    global _live_i
    _live_i += 1
    return "🔴" if _live_i % 2 else "⚫"


def status_chip(status: str) -> str:
    return {
        "active": "🟢 LIVE",
        "finishing": "🏁 YAKUN",
    }.get(status, "⚪")


def metric_card(icon: str, title: str, value: str, *, bar_pct: int | None = None) -> str:
    lines = [f"{icon}  <b>{he(title)}</b>", f"    <code>{he(value)}</code>"]
    if bar_pct is not None:
        lines.append(f"    <code>{glow_bar(bar_pct, 12)}</code>  <b>{bar_pct}%</b>")
    return "\n".join(lines)


def welcome_card(*, is_masul: bool, name: str) -> str:
    role = "Mas'ul paneli" if is_masul else "Ishchi rejimi"
    return (
        f"{banner(BRAND, icon='✨')}\n\n"
        f"👋  <b>{he(name)}</b>\n"
        f"<i>{he(role)}</i>\n\n"
        "┏━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        "┃  🚀  <b>Boshlash</b> — jarayon ochish\n"
        "┃  🏁  <b>Yakunlash</b> — hisobot + surat\n"
        "┃  📍  <b>Zonalar</b> — QR havolalar\n"
        "┃  📌  /id — Telegram ID\n"
        "┃  🔗  /guruh — guruh tekshiruv\n"
        "┗━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"<i>🕐 {he(display_now())}</i>"
    )


def worker_hint_card(*, name: str, session_active: bool) -> str:
    greet = f"👋  <b>{he(name)}</b>\n<i>Ishchi rejimi</i>\n\n"
    live_note = ""
    if session_active:
        live_note = (
            f"\n{sep('·')}\n"
            "🟢  <b>LIVE jarayon ochiq</b>\n"
            "👉  Ish guruhiga o'ting va tugmalardan foydalaning\n"
            f"{sep('·')}\n\n"
        )
    return (
        f"{banner(BRAND, icon='👷')}\n\n"
        f"{greet}"
        f"{live_note}"
        "┏━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃  🚀  <b>Boshlash</b> — mas'ul\n"
        f"┃  🏁  <b>Yakunlash</b> — mas'ul\n"
        f"┃  📍  <b>Zonalar</b> — QR havolalar\n"
        "┣━━━━━━━━━━━━━━━━━━━━━━━━┫\n"
        f"┃  1️⃣  Guruhda  <b>{he(BTN_JOIN)}</b>\n"
        f"┃  2️⃣  <b>{he(BTN_TRIP)}</b>\n"
        "┃  3️⃣  <b>📷 QR skaner</b> — kamera\n"
        "┗━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        "<i>⏱ Live taymer  ·  📦 Reys  ·  🏆 Reyting</i>\n\n"
        f"<i>🕐 {he(display_now())}</i>"
    )


def group_live_card(*, now: datetime | None = None, phase: str = "active") -> str:
    now = ensure_aware(now or now_dt())
    sess = storage.active_session
    if not sess:
        return f"{banner('HOLAT', icon='📊')}\n\n<i>Faol jarayon yo'q</i>"

    m = session_metrics(now)
    sid = sess.get("id", "—")
    pulse = live_pulse() if phase == "active" else "✅"

    lines = [
        banner("OMBORGA KIRITISH", icon=pulse),
        "",
        f"🪪  Sessiya   <code>#{sid}</code>",
        f"👤  Mas'ul   <b>{he(sess['masul_name'])}</b>",
        f"🕒  Boshlash <b>{fmt_hm(sess['start_time'])}</b>",
        f"📡  Holat    {status_chip(sess.get('status', 'active'))}",
        "",
    ]

    if storage.participants:
        lines.append(f"👷  <b>JAMOA</b>   {m.headcount} kishi")
        if m.open_trips:
            lines.append(f"<i>🔄 Ochiq reyslar: {m.open_trips}</i>")
        lines.append("")
        lines.append("<code>╭──────────────────────────╮</code>")
        for i, p in enumerate(
            sorted(storage.participants.values(), key=lambda x: x["join_time"]), 1
        ):
            ws = worker_stats(p["user_id"])
            trip_txt = f"  ·  📦 {ws['count']}" if ws["count"] else ""
            open_mark = "  🚛" if p["user_id"] in storage.active_trips else ""
            lines.append(
                f"<code>│</code> {rank_badge(i)}  <b>{he(p['full_name'])}</b>{open_mark}\n"
                f"<code>│</code>     ⏱  <b>{fmt_elapsed(p['join_time'], now)}</b>{trip_txt}"
            )
        lines.append("<code>╰──────────────────────────╯</code>")
    else:
        lines.extend(
            [
                sep("·"),
                "⚡  <b>Hozircha jamoa yo'q</b>",
                f"🔽  <b>{he(BTN_JOIN)}</b> ni bosing",
                sep("·"),
            ]
        )

    if phase == "active" and m.total_trips:
        trip_pct = min(100, m.total_trips * 5)
        lines.extend(
            [
                "",
                f"📦  Reyslar  <b>{m.total_trips}</b>  ·  📏  <b>{fmt_distance_m(m.total_distance)}</b>",
                f"<code>{glow_bar(trip_pct, 16)}</code>",
            ]
        )

    if phase == "active":
        proc_pct = min(100, m.process_sec // 36)
        lines.extend(
            [
                "",
                f"⏳  <b>Jarayon</b>  {fmt_duration(m.process_sec)}",
                f"<code>{glow_bar(proc_pct, 16)}</code>",
            ]
        )

    footer = f"<i>🕐 {he(display_now())}</i>"
    if phase == "active":
        footer = f"<i>🕐 {he(display_now())}  ·  {pulse} <b>LIVE</b></i>"
    lines.extend(["", sep(), footer])
    return "\n".join(lines)


def trip_started_card(*, bot_username: str) -> str:
    zones = []
    for code, z in storage.ZONES.items():
        link = f"https://t.me/{bot_username}?start=zone_{code}" if bot_username else f"zone_{code}"
        zones.append(
            f"<code>│</code>  📍  <b>{he(z['zone_name'])}</b>  "
            f"<i>{z['distance_meter']}m</i>\n"
            f"<code>│</code>      <code>{he(link)}</code>"
        )
    return (
        f"{banner('REYS BOSHLANDI', icon='🚛')}\n\n"
        "Zonaga boring va QR skaner qiling:\n"
        "<code>╭──────────────────────────╮</code>\n"
        + "\n".join(zones)
        + "\n<code>╰──────────────────────────╯</code>"
    )


def trip_complete_card(
    *,
    zone_name: str,
    distance_meter: int,
    duration_sec: int,
    worker_name: str,
) -> str:
    return (
        f"{banner('REYS YAKUN', icon='✅')}\n\n"
        f"👤  <b>{he(worker_name)}</b>\n"
        f"📍  <b>{he(zone_name)}</b>  ·  <i>{distance_meter} m</i>\n"
        f"⏱  <b>{fmt_duration_short(duration_sec)}</b>\n\n"
        f"<code>{glow_bar(min(100, duration_sec), 12)}</code>"
    )


def zones_list_card(*, bot_username: str) -> str:
    lines = [banner("QR ZONALAR", icon="📍"), ""]
    for code, z in storage.ZONES.items():
        link = (
            f"https://t.me/{bot_username}?start=zone_{code}"
            if bot_username
            else f"/start zone_{code}"
        )
        lines.append(
            f"▸  <b>{he(z['zone_name'])}</b>  <code>{he(code)}</code>\n"
            f"    📏 {z['distance_meter']}m\n"
            f"    <code>{he(link)}</code>\n"
        )
    lines.append(f"\n<i>🕐 {he(display_now())}</i>")
    return "\n".join(lines)


def photo_prompt(step: int, total: int, title: str, hint: str) -> str:
    pct = int(round(100 * step / max(total, 1)))
    return (
        f"📸  <b>SURAT {step}/{total}</b>\n"
        f"<code>{glow_bar(pct, 12)}</code>  <b>{step}/{total}</b>\n\n"
        f"<b>{he(title)}</b>\n"
        f"<i>{he(hint)}</i>\n\n"
        "⬇️  <b>Fotoni yuboring</b>"
    )


def final_report_card(*, finished_at: datetime | None = None) -> str:
    finished_at = finished_at or now_dt()
    m = session_metrics(finished_at)
    sess = storage.active_session or {}

    lines = [
        f"{banner('YAKUNIY HISOBOT', icon='📊', width=28)}\n",
        f"🪪  <code>#{sess.get('id', '—')}</code>  ·  👤  <b>{he(sess.get('masul_name', '—'))}</b>",
        f"🗓  {he(display_now())}  ·  👷  {m.headcount} kishi\n",
        metric_card("⏱", "Jarayon vaqti", fmt_duration(m.process_sec)),
        "",
        metric_card("🛠", "Odam-soat", fmt_duration(m.person_hours_sec)),
        "",
        metric_card("📦", "Jami reys", str(m.total_trips), bar_pct=min(100, m.total_trips * 4)),
        "",
        metric_card("📏", "Jami masofa", fmt_distance_m(m.total_distance)),
        "",
        metric_card(
            "⏱",
            "O'rtacha reys",
            fmt_duration(m.avg_trip_sec) if m.total_trips else "—",
        ),
        "",
        "🏆  <b>ISHCHILAR REYTINGI</b>",
        "<code>╭──────────────────────────╮</code>",
    ]

    ranked = ranked_workers()
    if not ranked:
        lines.append("<code>│</code>  <i>Ishtirokchi yo'q</i>")
    else:
        for i, p in enumerate(ranked, 1):
            ws = worker_stats(p["user_id"])
            if ws["count"]:
                lines.append(
                    f"<code>│</code> {rank_badge(i)}  <b>{he(p['full_name'])}</b>\n"
                    f"<code>│</code>      📦 {ws['count']}  ·  "
                    f"📏 {fmt_distance_m(ws['total_distance'])}  ·  "
                    f"⌀ {fmt_duration_short(ws['avg_time'])}"
                )
            else:
                lines.append(
                    f"<code>│</code> {rank_badge(i)}  <b>{he(p['full_name'])}</b>  "
                    f"<i>reys yo'q</i>"
                )
    lines.append("<code>╰──────────────────────────╯</code>")

    ph = storage.photos
    lines.extend(
        [
            "",
            sep(),
            "📸  <b>SURATLAR</b>",
            f"    Ombor ichida  {'✅' if ph.get('ombor') else '❌'}",
            f"    Bo'sh joy     {'✅' if ph.get('bosh_joy') else '❌'}",
            f"    Boshlang'ich  {'✅' if ph.get('boshlangich') else '❌'}",
            "",
            "✨  <b>OMBOR JARAYONI MUVAFFAQIYATLI YAKUNLANDI</b>  ✨",
        ]
    )
    return "\n".join(lines)


def photo_album_caption(kind: str) -> str:
    titles = {
        "ombor": "Ombordagi yuklar",
        "bosh_joy": "Bo'shagan joy",
        "boshlangich": "Boshlang'ich holat",
    }
    return f"📸  <b>{he(titles.get(kind, kind))}</b>"
