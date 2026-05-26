"""Hisob-kitob — har bir ishchi va guruh jami."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import storage
from time_util import ensure_aware, fmt_duration, now_dt


@dataclass
class SessionMetrics:
    process_sec: int
    person_hours_sec: int
    total_trips: int
    total_distance: int
    avg_trip_sec: int
    headcount: int
    open_trips: int


def session_metrics(end: datetime | None = None) -> SessionMetrics:
    """Guruh LIVE — barcha aktiv ishchilar jami."""
    end = end or now_dt()
    trips = storage.all_trips()
    total_dist = sum(t["distance_meter"] for t in trips)
    avg = sum(t["duration_sec"] for t in trips) // len(trips) if trips else 0
    open_n = sum(1 for s in storage.active_users() if s.get("active_trip"))
    ph = 0
    proc = 0
    for s in storage.active_users():
        ph += max(0, int((end - ensure_aware(s["start_time"])).total_seconds()))
        proc = max(proc, ph)
    return SessionMetrics(
        process_sec=proc,
        person_hours_sec=ph,
        total_trips=len(trips),
        total_distance=total_dist,
        avg_trip_sec=avg,
        headcount=len(storage.active_users()),
        open_trips=open_n,
    )


def worker_stats(user_id: int) -> dict[str, Any]:
    s = storage.get_session(user_id)
    user_trips = list((s or {}).get("trips") or [])
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


def ranked_workers() -> list[dict[str, Any]]:
    users = sorted(
        storage.active_users(),
        key=lambda s: (
            worker_stats(s["user_id"])["count"],
            worker_stats(s["user_id"])["total_distance"],
        ),
        reverse=True,
    )
    return [
        {
            "user_id": s["user_id"],
            "full_name": s["full_name"],
            "join_time": s["start_time"],
        }
        for s in users
    ]


def user_session_metrics(user_id: int, end: datetime | None = None) -> SessionMetrics:
    end = end or now_dt()
    s = storage.get_session(user_id)
    if not s:
        return SessionMetrics(0, 0, 0, 0, 0, 0, 0)
    trips = s.get("trips") or []
    proc = max(0, int((end - ensure_aware(s["start_time"])).total_seconds()))
    total_dist = sum(t["distance_meter"] for t in trips)
    avg = sum(t["duration_sec"] for t in trips) // len(trips) if trips else 0
    return SessionMetrics(
        process_sec=proc,
        person_hours_sec=proc,
        total_trips=len(trips),
        total_distance=total_dist,
        avg_trip_sec=avg,
        headcount=1,
        open_trips=1 if s.get("active_trip") else 0,
    )
