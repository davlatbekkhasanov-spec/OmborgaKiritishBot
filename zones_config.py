"""
Zonalar — yuk olish nuqtasidan masofa (metr).
Keyinroq muhokama qilib aniqlashtirish mumkin.

Qo'shimcha «см» / balandlik / zina — hozircha nomda eslatma sifatida.
"""

from __future__ import annotations

from typing import Any

# zone_code → { zone_name, distance_meter }
ZONES: dict[str, dict[str, Any]] = {
    "SKLAD_1": {
        "zone_name": "Склад 1",
        "distance_meter": 46,
        "note": "7 см (qo'shimcha)",
    },
    "SKLAD_2": {
        "zone_name": "Склад 2",
        "distance_meter": 41,
        "note": "7 см",
    },
    "SKLAD_3": {
        "zone_name": "Склад 3",
        "distance_meter": 38,
        "note": "8 см",
    },
    "SKLAD_4": {
        "zone_name": "Склад 4",
        "distance_meter": 32,
        "note": "5 см",
    },
    "SKLAD_5": {
        "zone_name": "Склад 5",
        "distance_meter": 24,
        "note": "8 см",
    },
    "SKLAD_6": {
        "zone_name": "Склад 6",
        "distance_meter": 19,
        "note": "7 см",
    },
    "SKLAD_FOTO_BUMAGA": {
        "zone_name": "Склад фото бумага",
        "distance_meter": 25,
        "note": "10 см",
    },
    "SKLAD_7": {
        "zone_name": "Склад 7",
        "distance_meter": 27,
    },
    "SKLAD_RAMKA_N": {
        "zone_name": "Склад рамка Н",
        "distance_meter": 37,
    },
    "SKLAD_7_ZAL": {
        "zone_name": "Склад 7 Зал",
        "distance_meter": 35,
        "note": "6 см",
    },
    "BUDKA": {
        "zone_name": "Будка",
        "distance_meter": 15,
        "note": "3 см",
    },
    "SKLAD_BALKON_ZAL_1": {
        "zone_name": "Склад балкон Зал 1",
        "distance_meter": 35,
        "note": "balandlik 5m 7sm, zina bor",
    },
    "SKLAD_BALKON_ZAL_2": {
        "zone_name": "Склад балкон Зал 2",
        "distance_meter": 46,
        "note": "balandlik 5m 7sm, zina bor",
    },
    "SKLAD_8": {
        "zone_name": "Склад 8",
        "distance_meter": 52,
        "note": "6 см",
    },
    "TUNEL_1": {
        "zone_name": "Тунел 1",
        "distance_meter": 53,
    },
    "TUNEL_2": {
        "zone_name": "Тунел 2",
        "distance_meter": 79,
    },
}
