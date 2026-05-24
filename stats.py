"""Hisob-kitob — final hisobot."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import storage
from time_util import fmt_distance_m, fmt_duration_long, fmt_duration_short


def _session_end() -> datetime:
    return datetime.now()


def process_duration_sec() -> int:
    sess = storage.active_session
    if not sess:
        return 0
    start = sess["start_time"]
    return max(0, int((_session_end() - start).total_seconds()))


def person_hours_sec() -> int:
    end = _session_end()
    total = 0
    for p in storage.participants.values():
        total += max(0, int((end - p["join_time"]).total_seconds()))
    return total


def worker_stats(user_id: int) -> dict[str, Any]:
    user_trips = [t for t in storage.trips if t["user_id"] == user_id]
    count = len(user_trips)
    if not count:
        return {
            "count": 0,
            "total_time": 0,
            "avg_time": 0,
            "total_distance": 0,
            "min_time": 0,
            "max_time": 0,
        }
    durations = [t["duration_sec"] for t in user_trips]
    return {
        "count": count,
        "total_time": sum(durations),
        "avg_time": sum(durations) // count,
        "total_distance": sum(t["distance_meter"] for t in user_trips),
        "min_time": min(durations),
        "max_time": max(durations),
    }


def build_final_report() -> str:
    sess = storage.active_session
    if not sess:
        return "Sessiya yo'q"

    proc_sec = process_duration_sec()
    total_trips = len(storage.trips)
    total_dist = sum(t["distance_meter"] for t in storage.trips)
    avg_trip = (
        sum(t["duration_sec"] for t in storage.trips) // total_trips
        if total_trips
        else 0
    )

    lines = [
        "📊 OMBORGA KIRITISH YAKUNLANDI",
        "",
        f"⏱ Jarayon vaqti: {fmt_duration_long(proc_sec)}",
        f"👥 Qatnashganlar: {len(storage.participants)}",
        f"🛠 Jami odam-soat: {fmt_duration_long(person_hours_sec())}",
        "",
        f"📦 Jami reys: {total_trips}",
        f"📏 Jami masofa: {fmt_distance_m(total_dist)}",
        f"⏱ O'rtacha reys: {fmt_duration_long(avg_trip)}",
        "",
        "👷 Ishchilar:",
    ]

    ranked = sorted(
        storage.participants.values(),
        key=lambda p: worker_stats(p["user_id"])["count"],
        reverse=True,
    )
    for i, p in enumerate(ranked, 1):
        ws = worker_stats(p["user_id"])
        if ws["count"]:
            lines.append(
                f"{i}. {p['full_name']} — {ws['count']} reys / "
                f"{fmt_distance_m(ws['total_distance'])} / "
                f"avg {fmt_duration_short(ws['avg_time'])}"
            )
        else:
            lines.append(f"{i}. {p['full_name']} — reys yo'q")

    ph = storage.photos
    lines.extend(
        [
            "",
            f"📸 Boshlang'ich rasm: {'✅' if ph.get('boshlangich') else '❌'}",
            f"📸 Ombordagi rasm: {'✅' if ph.get('ombor') else '❌'}",
            f"📸 Bo'shagan joy rasm: {'✅' if ph.get('bosh_joy') else '❌'}",
        ]
    )
    return "\n".join(lines)
