"""RAM saqlash (PostgreSQL keyinroq ulanadi)."""

from __future__ import annotations

from typing import Any

from time_util import ensure_aware, now_dt

from zones_config import ZONES

active_session: dict[str, Any] | None = None
participants: dict[int, dict[str, Any]] = {}
# Yakunlangan reyslar
trips: list[dict[str, Any]] = []
# user_id -> ochiq reys
active_trips: dict[int, dict[str, Any]] = {}
# session photos: boshlangich | ombor | bosh_joy
photos: dict[str, str] = {}

_trip_id = 0
_session_id = 0


def reset_session() -> None:
    global active_session, _trip_id
    active_session = None
    participants.clear()
    trips.clear()
    active_trips.clear()
    photos.clear()
    _trip_id = 0


def next_session_id() -> int:
    global _session_id
    _session_id += 1
    return _session_id


def has_active_session() -> bool:
    return active_session is not None and active_session.get("status") == "active"


def is_finishing() -> bool:
    return active_session is not None and active_session.get("status") == "finishing"


def can_manage(user_id: int) -> bool:
    """Mas'ul yoki admin."""
    from config import is_admin

    if is_admin(user_id):
        return True
    sess = active_session
    if not sess:
        return False
    return int(sess.get("masul_id", 0)) == int(user_id)


def is_participant(user_id: int) -> bool:
    return user_id in participants


def next_trip_id() -> int:
    global _trip_id
    _trip_id += 1
    return _trip_id


def add_masul_as_participant(user_id: int, full_name: str) -> None:
    if user_id in participants:
        return
    participants[user_id] = {
        "user_id": user_id,
        "full_name": full_name,
        "join_time": now_dt(),
    }


def try_join(user_id: int, full_name: str) -> tuple[bool, str]:
    if not has_active_session():
        return False, "Jarayon aktiv emas."
    if user_id in participants:
        return False, "Siz allaqachon ro'yxatdasiz."
    participants[user_id] = {
        "user_id": user_id,
        "full_name": full_name,
        "join_time": now_dt(),
    }
    return True, "Siz qatnashdingiz ✅"


def try_start_trip(user_id: int) -> tuple[bool, str]:
    if not has_active_session():
        return False, "Jarayon aktiv emas."
    if not is_participant(user_id):
        return False, "Avval «Qatnashish» tugmasini bosing."
    if user_id in active_trips:
        return False, "Sizda ochiq reys bor. Avval QR skaner qiling."
    tid = next_trip_id()
    active_trips[user_id] = {
        "id": tid,
        "user_id": user_id,
        "trip_start_time": now_dt(),
    }
    return True, "Reys boshlandi. Zonada QR skaner qiling 📱"


def try_complete_trip(user_id: int, zone_code: str) -> tuple[bool, str]:
    if not has_active_session():
        return False, "Jarayon aktiv emas."
    zone = ZONES.get(zone_code.upper())
    if not zone:
        return False, f"Noma'lum zona: {zone_code}"
    open_trip = active_trips.get(user_id)
    if not open_trip:
        return False, "Ochiq reys yo'q. Avval «Reys oldim» bosing."
    end = now_dt()
    start = ensure_aware(open_trip["trip_start_time"])
    duration_sec = max(0, int((end - start).total_seconds()))
    record = {
        "id": open_trip["id"],
        "user_id": user_id,
        "trip_start_time": start,
        "trip_end_time": end,
        "zone_code": zone_code.upper(),
        "zone_name": zone["zone_name"],
        "duration_sec": duration_sec,
        "distance_meter": zone["distance_meter"],
    }
    trips.append(record)
    del active_trips[user_id]
    return True, record


def parse_zone_payload(text: str | None) -> str | None:
    """/start zone_OMBOR_A"""
    from qr_parse import parse_zone_from_text

    if not text:
        return None
    raw = text.strip()
    if raw.lower().startswith("zone_"):
        return raw[5:].strip().upper()
    return parse_zone_from_text(raw)
