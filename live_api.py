"""Live ombor sessiyalari — JSON snapshot (MVP dashboard)."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import storage
from stats import metrics_from_session
from time_util import ensure_aware, fmt_duration, fmt_duration_short, now_dt


def live_dash_token() -> str:
    return (
        os.getenv("LIVE_DASH_TOKEN")
        or os.getenv("DASH_TOKEN")
        or os.getenv("YORDAMCHI_HUB_SECRET")
        or ""
    ).strip()


def live_token_ok(token: str) -> bool:
    expected = live_dash_token()
    if not expected:
        return False
    return (token or "").strip() == expected


def _iso(dt: datetime | None) -> str | None:
    if not dt:
        return None
    return ensure_aware(dt).isoformat()


def _trip_row(t: dict[str, Any]) -> dict[str, Any]:
    leg = int(t.get("leg_meter", t.get("distance_meter", 0)) or 0)
    dur = int(t.get("duration_sec", 0) or 0)
    return {
        "zone_code": t.get("zone_code"),
        "zone_name": t.get("zone_name"),
        "leg_meter": leg,
        "duration_sec": dur,
        "duration": fmt_duration_short(dur),
    }


def _empty_row(seg: dict[str, Any]) -> dict[str, Any]:
    return {
        "from_zone": seg.get("from_zone"),
        "from_zone_name": seg.get("from_zone_name"),
        "meter": int(seg.get("meter", 0) or 0),
    }


def _worker_snapshot(sess: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    now = now or now_dt()
    m = metrics_from_session(sess, now)
    trips = [_trip_row(t) for t in sess.get("trips") or []]
    empty = [_empty_row(s) for s in sess.get("empty_segments") or []]
    open_trip = sess.get("active_trip")
    reys_pct = min(100, m.total_trips * 8) if m.total_trips else 0
    return {
        "user_id": sess.get("user_id"),
        "full_name": sess.get("full_name") or "Noma'lum",
        "session_id": sess.get("id"),
        "start_time": _iso(sess.get("start_time")),
        "ish_vaqti_sec": m.process_sec,
        "ish_vaqti": fmt_duration(m.process_sec),
        "reys_count": m.total_trips,
        "reys_bar_pct": reys_pct,
        "yuk_masofa": storage.total_loaded_distance(sess),
        "yuksiz_masofa": int(sess.get("empty_distance_meter", 0) or 0),
        "dam_sec": storage.total_break_sec(sess),
        "dam": fmt_duration(storage.total_break_sec(sess)),
        "open_trip": bool(open_trip),
        "trips": trips,
        "empty_segments": empty,
    }


def build_live_snapshot() -> dict[str, Any]:
    now = now_dt()
    workers = [_worker_snapshot(s, now=now) for s in storage.active_users()]
    workers.sort(key=lambda w: (-w["reys_count"], -w["yuk_masofa"], w["full_name"]))
    total_trips = sum(w["reys_count"] for w in workers)
    total_dist = sum(w["yuk_masofa"] for w in workers)
    return {
        "ok": True,
        "updated_at": _iso(now),
        "display_time": now.strftime("%d.%m.%Y  %H:%M:%S"),
        "active_count": len(workers),
        "total_trips": total_trips,
        "total_distance": total_dist,
        "workers": workers,
    }
