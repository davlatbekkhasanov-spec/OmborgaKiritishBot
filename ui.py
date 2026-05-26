"""Premium Telegram HTML kartalar."""

from __future__ import annotations

import html as html_lib
from datetime import datetime
from typing import Any

import storage
from stats import ranked_workers, session_metrics, user_session_metrics, worker_stats
from texts import BRAND, BTN_PICK_ZONE, BTN_START_MOVE, BTN_TRIP
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


def metric_card(icon: str, title: str, value: str, *, bar_pct: int | None = None) -> str:
    lines = [f"{icon}  <b>{he(title)}</b>", f"    <code>{he(value)}</code>"]
    if bar_pct is not None:
        lines.append(f"    <code>{glow_bar(bar_pct, 12)}</code>  <b>{bar_pct}%</b>")
    return "\n".join(lines)


def main_hint_card(*, name: str, user_id: int) -> str:
    active = storage.has_user_session(user_id)
    live_note = ""
    if active:
        live_note = (
            f"\n{sep('·')}\n"
            "🟢  <b>Sizning jarayoningiz aktiv</b>\n"
            f"{sep('·')}\n\n"
        )
    return (
        f"{banner(BRAND, icon='👷')}\n\n"
        f"👋  <b>{he(name)}</b>\n"
        f"<i>Har bir ishchi mustaqil ishlaydi</i>\n"
        f"{live_note}"
        "┏━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃  1️⃣  <b>{he(BTN_START_MOVE)}</b>\n"
        f"┃      Yukingiz <b>1 ta rasm</b> — shu bilan boshlanadi\n"
        f"┃  2️⃣  <b>{he(BTN_TRIP)}</b> → yuk bilan manzil (QR/zona)\n"
        f"┃  3️⃣  Keyingi reysgacha — <b>dam</b> va <b>yuksiz</b> avto\n"
        f"┃  4️⃣  <b>🏁 Yakunlash</b>\n"
        "┗━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        "<i>📣 Guruhda hammangiz statistikasi ko'rinadi</i>\n\n"
        f"<i>🕐 {he(display_now())}</i>"
    )


def start_photo_prompt() -> str:
    return (
        f"{banner('BOSHLASH', icon='📸')}\n\n"
        "O'zingiz olib ketadigan <b>yuklarning</b> bitta aniq "
        "fotosuratini yuboring.\n\n"
        "<i>Boshqa ishchi ham xohlasa — o'z rasmi bilan "
        "alohida boshlaydi.</i>"
    )


def session_started_card(*, name: str, session_id: int) -> str:
    return (
        f"{banner('ISHLASH BOSHLANDI', icon='✅')}\n\n"
        f"👤  <b>{he(name)}</b>\n"
        f"🪪  Sessiya <code>#{session_id}</code>\n\n"
        f"Endi <b>{he(BTN_TRIP)}</b> bosing va zonaga boring."
    )


def group_live_card(*, now: datetime | None = None, empty: bool = False) -> str:
    now = ensure_aware(now or now_dt())
    users = storage.active_users()
    if empty or not users:
        return (
            f"{banner('OMBOR LIVE', icon='📊')}\n\n"
            "<i>Hozircha aktiv ishchi yo'q</i>\n\n"
            f"📸  Shaxsiy chatda <b>{he(BTN_START_MOVE)}</b> — "
            "yuk rasmi bilan\n\n"
            f"<i>🕐 {he(display_now())}</i>"
        )

    m = session_metrics(now)
    pulse = live_pulse()
    lines = [
        banner("OMBOR LIVE", icon=pulse),
        "",
        f"👥  <b>{m.headcount}</b> kishi ishlayapti"
        f"  ·  📦 <b>{m.total_trips}</b> reys"
        f"  ·  📏 <b>{fmt_distance_m(m.total_distance)}</b>",
    ]
    if m.open_trips:
        lines.append(f"<i>🔄 Ochiq reys: {m.open_trips}</i>")

    ranked = ranked_workers()
    if ranked:
        lines.extend(["", "🏆  <b>REYS TAQSIMOTI</b>", "<code>╭──────────────────────────╮</code>"])
        for i, p in enumerate(ranked, 1):
            ws = worker_stats(p["user_id"])
            s = storage.get_session(p["user_id"])
            open_mark = " 🚛" if s and s.get("active_trip") else ""
            lines.append(
                f"<code>│</code> {rank_badge(i)}  <b>{he(p['full_name'])}</b>{open_mark}\n"
                f"<code>│</code>     📦 <b>{ws['count']}</b> reys"
                f"  ·  📏 {fmt_distance_m(ws['total_distance'])}"
                f"  ·  ⏱ {fmt_elapsed(p['join_time'], now)}"
            )
        lines.append("<code>╰──────────────────────────╯</code>")

    proc_pct = min(100, m.process_sec // 36) if m.process_sec else 0
    lines.extend(
        [
            "",
            f"⏳  <b>Eng uzoq ish</b>  {fmt_duration(m.process_sec)}",
            f"<code>{glow_bar(proc_pct, 16)}</code>",
            "",
            sep(),
            f"<i>🕐 {he(display_now())}  ·  {pulse} <b>LIVE</b></i>",
        ]
    )
    return "\n".join(lines)


def trip_complete_card(
    *,
    zone_name: str,
    distance_meter: int,
    duration_sec: int,
    worker_name: str,
    leg_meter: int | None = None,
    horizontal_meter: int | None = None,
) -> str:
    leg = leg_meter if leg_meter is not None else distance_meter
    dist_line = f"📏  Yuk bilan manzil: <b>{leg} m</b>"
    if horizontal_meter is not None and horizontal_meter != leg:
        dist_line += f"\n    <i>Goriz. {horizontal_meter} m</i>"
    return (
        f"{banner('REYS YAKUN', icon='✅')}\n\n"
        f"👤  <b>{he(worker_name)}</b>\n"
        f"📦  <b>{he(zone_name)}</b> — yuk qo'yildi\n"
        f"{dist_line}\n"
        f"⏱  Reys vaqti: <b>{fmt_duration_short(duration_sec)}</b>\n\n"
        f"<i>Keyingi {he(BTN_TRIP)}gacha — dam va yuksiz yurish "
        f"avtomatik hisoblanadi</i>\n\n"
        f"<code>{glow_bar(min(100, duration_sec), 12)}</code>"
    )


def zones_list_card(*, bot_username: str) -> str:
    lines = [banner("QR ZONALAR", icon="📦"), ""]
    for code, z in storage.ZONES.items():
        link = (
            f"https://t.me/{bot_username}?start=zone_{code}"
            if bot_username
            else f"/start zone_{code}"
        )
        from zones_config import zone_leg_meter

        leg = zone_leg_meter(z)
        lines.append(
            f"▸  <b>{he(z['zone_name'])}</b>  <code>{he(code)}</code>\n"
            f"    📏 yuk bilan <b>{leg}m</b>\n"
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


def final_report_card(
    sess: dict[str, Any], *, finished_at: datetime | None = None
) -> str:
    finished_at = finished_at or now_dt()
    uid = sess["user_id"]
    m = user_session_metrics(uid, finished_at)

    lines = [
        f"{banner('YAKUNIY HISOBOT', icon='📊', width=28)}\n",
        f"👤  <b>{he(sess['full_name'])}</b>\n"
        f"🪪  <code>#{sess.get('id', '—')}</code>  ·  "
        f"🕒  {fmt_hm(sess['start_time'])}\n",
        metric_card("⏱", "Ish vaqti", fmt_duration(m.process_sec)),
        "",
        metric_card("📦", "Reyslar", str(m.total_trips), bar_pct=min(100, m.total_trips * 8)),
        "",
        metric_card(
            "📏",
            "Yuk bilan masofa",
            fmt_distance_m(storage.total_loaded_distance(sess)),
        ),
        "",
        metric_card(
            "🚶",
            "Yuksiz masofa",
            fmt_distance_m(int(sess.get("empty_distance_meter", 0))),
        ),
        "",
        metric_card(
            "☕",
            "Dam olish (reyslar orasi)",
            fmt_duration(storage.total_break_sec(sess)),
        ),
        "",
        "📦  <b>REYSLAR (yuk bilan)</b>",
        "<code>╭──────────────────────────╮</code>",
    ]

    trips = sess.get("trips") or []
    if not trips:
        lines.append("<code>│</code>  <i>Reys yo'q</i>")
    else:
        for i, t in enumerate(trips, 1):
            leg = t.get("leg_meter", t.get("distance_meter", 0))
            lines.append(
                f"<code>│</code> {i}.  <b>{he(t['zone_name'])}</b>  ·  "
                f"<b>{leg}m</b>  ·  ⏱ {fmt_duration_short(t['duration_sec'])}"
            )
    lines.append("<code>╰──────────────────────────╯</code>")

    empty_segs = sess.get("empty_segments") or []
    if empty_segs:
        lines.extend(["", "🚶  <b>YUKSIZ YURISH</b>", "<code>╭──────────────────────────╮</code>"])
        for i, seg in enumerate(empty_segs, 1):
            lines.append(
                f"<code>│</code> {i}.  {he(seg.get('from_zone_name', seg.get('from_zone')))} "
                f"→ yuk olish  ·  <b>{seg['meter']}m</b>"
            )
        lines.append("<code>╰──────────────────────────╯</code>")

    ph = sess.get("finish_photos") or {}
    lines.extend(
        [
            "",
            sep(),
            "📸  <b>SURATLAR</b>",
            f"    Boshlash (yuk)  {'✅' if sess.get('start_photo') else '❌'}",
            f"    Ombor           {'✅' if ph.get('ombor') else '❌'}",
            f"    Bo'sh joy       {'✅' if ph.get('bosh_joy') else '❌'}",
            "",
            "✨  <b>ISH MUVAFFAQIYATLI YAKUNLANDI</b>  ✨",
        ]
    )
    return "\n".join(lines)


def photo_album_caption(kind: str, *, worker_name: str = "") -> str:
    titles = {
        "start": "Boshlash — yuk",
        "ombor": "Ombordagi yuklar",
        "bosh_joy": "Bo'shagan joy",
    }
    who = f" · {he(worker_name)}" if worker_name else ""
    return f"📸  <b>{he(titles.get(kind, kind))}</b>{who}"


def group_user_started_caption(*, name: str, session_id: int) -> str:
    return f"🟢  <b>{he(name)}</b> ish boshladi  ·  <code>#{session_id}</code>"
