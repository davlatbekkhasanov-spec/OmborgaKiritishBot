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
