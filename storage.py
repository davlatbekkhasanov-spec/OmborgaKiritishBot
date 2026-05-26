"""RAM — har bir ishchi o'z sessiyasida (PostgreSQL keyinroq)."""

from __future__ import annotations

from typing import Any

from time_util import ensure_aware, now_dt
from zones_config import ZONES  # noqa: F401 — keyboards/storage.ZONES

# user_id -> shaxsiy sessiya
user_sessions: dict[int, dict[str, Any]] = {}

# Guruh LIVE paneli (barcha ishchilar jamlanmasi)
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
    }


def reset_all() -> None:
    """To'liq tozalash (test)."""
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


# ——— Eski API (migratsiya uchun qisqa nomlar) ———

def has_active_session() -> bool:
    return any_active_users()


def is_participant(user_id: int) -> bool:
    return has_user_session(user_id)


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
    tid = next_trip_id()
    s["active_trip"] = {
        "id": tid,
        "user_id": user_id,
        "trip_start_time": now_dt(),
    }
    return True, "Reys boshlandi ✅"


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
    record = {
        "id": open_trip["id"],
        "user_id": user_id,
        "trip_start_time": start,
        "trip_end_time": end,
        "zone_code": zone_code.upper(),
        "zone_name": zone["zone_name"],
        "duration_sec": duration_sec,
        "horizontal_meter": zone["horizontal_meter"],
        "effort_meter": zone["effort_meter"],
        "distance_meter": zone["effort_meter"],
    }
    s.setdefault("trips", []).append(record)
    s["active_trip"] = None
    return True, record


def begin_user_finish(user_id: int) -> tuple[bool, str]:
    s = get_session(user_id)
    if not s or s.get("status") != "active":
        return False, "Aktiv jarayon yo'q."
    if s.get("active_trip"):
        return False, "Ochiq reys bor — avval zonani yoping."
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
