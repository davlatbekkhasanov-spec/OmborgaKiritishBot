"""
Zonalar — yuk olish nuqtasidan.
Ekvivalent masofa = gorizontal + (balandlik × STAIR_FACTOR)
"""

from __future__ import annotations

from typing import Any

# Qo'lda yuk + zina: 1 m baland ≈ N m gorizontal mehnat
STAIR_FACTOR = 4


def _zone(
    zone_name: str,
    horizontal_meter: float,
    *,
    height_meter: float = 0.0,
    note: str = "",
) -> dict[str, Any]:
    effort = int(round(horizontal_meter + height_meter * STAIR_FACTOR))
    return {
        "zone_name": zone_name,
        "horizontal_meter": int(horizontal_meter),
        "height_meter": height_meter,
        "distance_meter": effort,  # hisob-kitobda ekvivalent
        "effort_meter": effort,
        "note": note,
    }


ZONES: dict[str, dict[str, Any]] = {
    "SKLAD_1": _zone("Склад 1", 46, height_meter=0.07, note="7 sm"),
    "SKLAD_2": _zone("Склад 2", 41, height_meter=0.07, note="7 sm"),
    "SKLAD_3": _zone("Склад 3", 38, height_meter=0.08, note="8 sm"),
    "SKLAD_4": _zone("Склад 4", 32, height_meter=0.05, note="5 sm"),
    "SKLAD_5": _zone("Склад 5", 24, height_meter=0.08, note="8 sm"),
    "SKLAD_6": _zone("Склад 6", 19, height_meter=0.07, note="7 sm"),
    "SKLAD_FOTO_BUMAGA": _zone("Склад фото бумага", 25, height_meter=0.10, note="10 sm"),
    "SKLAD_7": _zone("Склад 7", 27),
    "SKLAD_RAMKA_N": _zone("Склад рамка Н", 37),
    "SKLAD_7_ZAL": _zone("Склад 7 Зал", 35, height_meter=0.06, note="6 sm"),
    "BUDKA": _zone("Будка", 15, height_meter=0.03, note="3 sm"),
    "SKLAD_BALKON_ZAL_1": _zone(
        "Склад балкон Зал 1", 35, height_meter=5.7, note="zina bor"
    ),
    "SKLAD_BALKON_ZAL_2": _zone(
        "Склад балкон Зал 2", 46, height_meter=5.7, note="zina bor"
    ),
    "SKLAD_8": _zone("Склад 8", 52, height_meter=0.06, note="6 sm"),
    "TUNEL_1": _zone("Тунел 1", 53),
    "TUNEL_2": _zone("Тунел 2", 79),
}


def zone_leg_meter(zone: dict[str, Any]) -> int:
    """Bitta yo'nalish (yuk olish nuqtasi ↔ zona)."""
    return int(zone.get("effort_meter", zone.get("distance_meter", 0)))


def zone_round_trip_meter(zone: dict[str, Any]) -> int:
    """Borish + yuk bilan qaytish."""
    return zone_leg_meter(zone) * 2


def zone_deep_link(bot_username: str, zone_code: str) -> str:
    """QR chop etish — kamera odatda https ni yaxshi ochadi."""
    return bot_web_deep_link(bot_username, f"zone_{zone_code}")


TELEGRAM_ANDROID_PACKAGE = "org.telegram.messenger"


def bot_web_deep_link(bot_username: str, start_param: str) -> str:
    user = (bot_username or "").strip().lstrip("@")
    return f"https://t.me/{user}?start={start_param}"


def bot_app_deep_link(bot_username: str, start_param: str) -> str:
    """
    NFC stiker — tg:// (ba'zi telefonlarda baribir brauzer ochiladi).
    Masalan: tg://resolve?domain=Bot&start=reys
    """
    user = (bot_username or "").strip().lstrip("@")
    return f"tg://resolve?domain={user}&start={start_param}"


def bot_android_intent_deep_link(bot_username: str, start_param: str) -> str:
    """
    Android NFC — Telegram ilovasini majburiy ochadi (brauzer emas).
    NFC Tools → Other → Custom URL / URI — shu qatorni to'liq yozing.
    """
    user = (bot_username or "").strip().lstrip("@")
    return (
        f"intent://resolve?domain={user}&start={start_param}"
        "#Intent;scheme=tg;package=org.telegram.messenger;end"
    )
