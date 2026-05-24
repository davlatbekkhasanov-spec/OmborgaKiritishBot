# Zonalar + QR chop etish

## Ekvivalent masofa

```
ekvivalent = gorizontal (m) + balandlik (m) × 4
```

`STAIR_FACTOR = 4` — `zones_config.py` da o'zgartirish mumkin.

| Zona | Gor (m) | Baland | Ekv (m) |
|------|---------|--------|---------|
| Склад 1 | 46 | 0.07 | 46 |
| Склад 2 | 41 | 0.07 | 41 |
| Склад 3 | 38 | 0.08 | 38 |
| Склад 4 | 32 | 0.05 | 32 |
| Склад 5 | 24 | 0.08 | 24 |
| Склад 6 | 19 | 0.07 | 19 |
| Склад фото бумага | 25 | 0.10 | 25 |
| Склад 7 | 27 | — | 27 |
| Склад рамка Н | 37 | — | 37 |
| Склад 7 Зал | 35 | 0.06 | 35 |
| Будка | 15 | 0.03 | 15 |
| Склад балкон Зал 1 | 35 | 5.7 | **58** |
| Склад балкон Зал 2 | 46 | 5.7 | **69** |
| Склад 8 | 52 | 0.06 | 52 |
| Тунел 1 | 53 | — | 53 |
| Тунел 2 | 79 | — | 79 |

## QR stikerlarni chop etish

### 1-usul — PNG fayllar (tavsiya)

Kompyuterda (bot papkasida):

```bash
pip install -r requirements-qr.txt
python scripts/generate_zone_qr.py --bot SIZNING_BOT_USERNAME
```

`qr_print/` papkasida:
- `SKLAD_1.png` … `TUNEL_2.png` — har zona alohida
- `chop_etish.html` — brauzerdan Ctrl+P, A4
- `havolalar.txt` — barcha havolalar

Stikerlarni zonaga yopishtiring.

### 2-usul — Telegram

Mas'ul shaxsiy chatda: **`/qrprint`** — barcha havolalar matn bo‘lib keladi (onlayn QR generatorga qo‘yish mumkin).

### QR format

```
https://t.me/BOT_USERNAME?start=zone_SKLAD_1
```

Telefon kamerasi yoki Telegram skaner — bot ochiladi, reys yopiladi.
