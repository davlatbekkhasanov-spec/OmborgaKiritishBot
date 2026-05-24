"""Hisob-kitob — UI uchun strukturalangan."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import storage
from time_util import fmt_distance_m, fmt_duration, fmt_duration_short, now_dt


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
    end = end or now_dt()
    sess = storage.active_session
    proc = 0
    if sess:
        proc = max(0, int((end - sess["start_time"]).total_seconds()))
    ph = 0
    for p in storage.participants.values():
        ph += max(0, int((end - p["join_time"]).total_seconds()))
    trips = storage.trips
    total_dist = sum(t["distance_meter"] for t in trips)
    avg = sum(t["duration_sec"] for t in trips) // len(trips) if trips else 0
    return SessionMetrics(
        process_sec=proc,
        person_hours_sec=ph,
        total_trips=len(trips),
        total_distance=total_dist,
        avg_trip_sec=avg,
        headcount=len(storage.participants),
        open_trips=len(storage.active_trips),
    )


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


def ranked_workers() -> list[dict[str, Any]]:
    return sorted(
        storage.participants.values(),
        key=lambda p: (worker_stats(p["user_id"])["count"], worker_stats(p["user_id"])["total_distance"]),
        reverse=True,
    )
