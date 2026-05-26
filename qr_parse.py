"""QR matndan zona kodini ajratish."""

from __future__ import annotations

import re


def parse_zone_from_text(text: str) -> str | None:
    raw = (text or "").strip()
    if not raw:
        return None
    m = re.search(r"start=zone_([A-Za-z0-9_]+)", raw, re.I)
    if m:
        return m.group(1).upper()
    m = re.search(r"zone_([A-Za-z0-9_]+)", raw, re.I)
    if m:
        return m.group(1).upper()
    if re.fullmatch(r"[A-Z0-9_]{2,32}", raw.upper()):
        return raw.upper()
    return None


def parse_reys_from_text(text: str) -> bool:
    """NFC/QR matndan reys boshlash (start=reys)."""
    raw = (text or "").strip()
    if not raw:
        return False
    if raw.lower() in ("reys", "/start reys"):
        return True
    return bool(re.search(r"(?:^|[?&])start=reys(?:\s|$|&)", raw, re.I))
