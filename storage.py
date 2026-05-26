"""RAM — har bir ishchi o'z sessiyasida (PostgreSQL keyinroq ulanadi)."""

from __future__ import annotations

from typing import Any

from time_util import ensure_aware, fmt_duration_short, now_dt
from zones_config import ZONES, zone_leg_meter  # noqa: F401

user_sessions: dict[int, dict[str, Any]] = {}
group_panel: dict[str, Any] = {}

_trip_id = 0
_session_id = 0


def _new_session_dict(
    user_id: int, full_name: str, start_photo: str
) -> dict[str, Any]:
    return {
        "id": next_session_id(),
        "user_id": user_id,
        "full_name": full_name,
        "start_time": now_dt(),
        "status": "active",
        "start_photo": start_photo,
        "trips": [],
        "active_trip": None,
        "finish_photos": {},
        "breaks": [],
        "empty_distance_meter": 0,
        "empty_segments": [],
        "last_trip_end_at": None,
        "last_zone_code": None,
    }


def reset_all() -> None:
    user_sessions.clear()
    group_panel.clear()
    global _trip_id
    _trip_id = 0


def next_session_id() -> int:
    global _session_id
    _session_id += 1
    return _session_id


def next_trip_id() -> int:
    global _trip_id
    _trip_id += 1
    return _trip_id


def get_session(user_id: int) -> dict[str, Any] | None:
    return user_sessions.get(user_id)


def has_user_session(user_id: int) -> bool:
    s = get_session(user_id)
    return s is not None and s.get("status") == "active"


def is_finishing(user_id: int) -> bool:
    s = get_session(user_id)
    return s is not None and s.get("status") == "finishing"


def any_active_users() -> bool:
    return any(s.get("status") == "active" for s in user_sessions.values())


def active_users() -> list[dict[str, Any]]:
    return [s for s in user_sessions.values() if s.get("status") == "active"]


def all_trips() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for s in user_sessions.values():
        out.extend(s.get("trips") or [])
    return out


def user_has_open_trip(user_id: int) -> bool:
    s = get_session(user_id)
    return bool(s and s.get("active_trip"))


def has_active_session() -> bool:
    return any_active_users()


def is_participant(user_id: int) -> bool:
    return has_user_session(user_id)


def total_break_sec(sess: dict[str, Any]) -> int:
    return sum(int(b.get("duration_sec", 0)) for b in sess.get("breaks") or [])


def total_loaded_distance(sess: dict[str, Any]) -> int:
    return sum(int(t.get("distance_meter", 0)) for t in sess.get("trips") or [])


def _apply_interval_since_last_trip(s: dict[str, Any], now) -> str:
    """
    Oldingi reys yakunlangandan keyin yangi reysgacha:
    - vaqt → dam olish (avtomatik)
    - oxirgi zona → yuk olish nuqtasi: yuksiz masofa
    """
    last_end = s.get("last_trip_end_at")
    last_zone = s.get("last_zone_code")
    if not last_end or not last_zone:
        return ""

    last_end = ensure_aware(last_end)
    sec = max(0, int((now - last_end).total_seconds()))
    empty_m = 0
    zone = ZONES.get(str(last_zone).upper())
    if zone:
        empty_m = zone_leg_meter(zone)

    if sec > 0:
        s.setdefault("breaks", []).append(
            {
                "start": last_end,
                "end": now,
                "duration_sec": sec,
                "after_zone": last_zone,
            }
        )
    if empty_m > 0:
        s["empty_distance_meter"] = int(s.get("empty_distance_meter", 0)) + empty_m
        s.setdefault("empty_segments", []).append(
            {
                "from_zone": last_zone,
                "from_zone_name": zone["zone_name"],
                "meter": empty_m,
            }
        )

    s["last_trip_end_at"] = None
    s["last_zone_code"] = None

    parts: list[str] = []
    if sec > 0:
        parts.append(f"☕ Dam (avto): {fmt_duration_short(sec)}")
    if empty_m > 0:
        parts.append(f"📏 Yuksiz: {empty_m} m")
    return "\n".join(parts)


def try_begin_start(user_id: int) -> tuple[bool, str]:
    if has_user_session(user_id):
        return False, "Sizda allaqachon aktiv jarayon bor. Avval Yakunlash."
    if is_finishing(user_id):
        return False, "Yakunlash jarayonida. Suratlarni yuboring yoki /cancel"
    return True, ""


def activate_session(user_id: int, full_name: str, start_photo: str) -> dict[str, Any]:
    sess = _new_session_dict(user_id, full_name, start_photo)
    user_sessions[user_id] = sess
    return sess


def try_start_trip(user_id: int) -> tuple[bool, str]:
    s = get_session(user_id)
    if not s or s.get("status") != "active":
        return False, "Avval 📸 Boshlash — yukingiz rasmini yuboring."
    if s.get("active_trip"):
        return False, "Ochiq reys bor. Avval zonani yoping (QR yoki tanlash)."

    now = now_dt()
    interval_note = _apply_interval_since_last_trip(s, now)

    tid = next_trip_id()
    s["active_trip"] = {
        "id": tid,
        "user_id": user_id,
        "trip_start_time": now,
    }
    msg = "Reys boshlandi ✅"
    if interval_note:
        msg += f"\n\n{interval_note}"
    return True, msg


def try_complete_trip(user_id: int, zone_code: str) -> tuple[bool, str | dict[str, Any]]:
    s = get_session(user_id)
    if not s or s.get("status") != "active":
        return False, "Avval 📸 Boshlash bilan ishni boshlang."
    zone = ZONES.get(zone_code.upper())
    if not zone:
        return False, f"Noma'lum zona: {zone_code}"
    open_trip = s.get("active_trip")
    if not open_trip:
        return False, "Ochiq reys yo'q. Avval 📦 Reys oldim bosing."
    end = now_dt()
    start = ensure_aware(open_trip["trip_start_time"])
    duration_sec = max(0, int((end - start).total_seconds()))
    leg = zone_leg_meter(zone)
    record = {
        "id": open_trip["id"],
        "user_id": user_id,
        "trip_start_time": start,
        "trip_end_time": end,
        "zone_code": zone_code.upper(),
        "zone_name": zone["zone_name"],
        "duration_sec": duration_sec,
        "horizontal_meter": zone["horizontal_meter"],
        "effort_meter": leg,
        "leg_meter": leg,
        "distance_meter": leg,
    }
    s.setdefault("trips", []).append(record)
    s["active_trip"] = None
    s["last_trip_end_at"] = end
    s["last_zone_code"] = zone_code.upper()
    return True, record


def finalize_pending_interval(user_id: int) -> None:
    """Yakunlashdan oldin — oxirgi reysdan keyingi dam va yuksiz masofa."""
    s = get_session(user_id)
    if not s or s.get("active_trip"):
        return
    _apply_interval_since_last_trip(s, now_dt())


def begin_user_finish(user_id: int) -> tuple[bool, str]:
    s = get_session(user_id)
    if not s or s.get("status") != "active":
        return False, "Aktiv jarayon yo'q."
    if s.get("active_trip"):
        return False, "Ochiq reys bor — avval zonani yoping."
    finalize_pending_interval(user_id)
    s["status"] = "finishing"
    s["finish_photos"] = {}
    return True, ""


def cancel_user_finish(user_id: int) -> None:
    s = get_session(user_id)
    if s and s.get("status") == "finishing":
        s["status"] = "active"


def end_user_session(user_id: int) -> dict[str, Any] | None:
    return user_sessions.pop(user_id, None)


def parse_zone_payload(text: str | None) -> str | None:
    from qr_parse import parse_zone_from_text

    if not text:
        return None
    raw = text.strip()
    if raw.lower().startswith("zone_"):
        code = raw[5:].strip().upper()
        return code if code in ZONES else None
    code = parse_zone_from_text(raw)
    if code and code in ZONES:
        return code
    return None
