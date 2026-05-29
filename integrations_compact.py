"""Omborga — hub uchun qisqa xulosa."""

from __future__ import annotations

from typing import Any

import storage
from stats import user_session_metrics
from time_util import fmt_duration_short, now_dt


def compact_session_summary(sess: dict[str, Any]) -> str:
    uid = int(sess.get("user_id") or 0)
    trips = len(sess.get("trips") or [])
    dist = storage.total_loaded_distance(sess)
    br = storage.total_break_sec(sess)
    m = user_session_metrics(uid, now_dt())
    return (
        f"Reys {trips}, yuk {dist}m, ish {fmt_duration_short(m.process_sec)}, "
        f"dam {fmt_duration_short(br)}"
    )
