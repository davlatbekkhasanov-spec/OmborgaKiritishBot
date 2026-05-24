# 📦 Omborga Kiritish Bot

**GLOBUS · OMBOR LIVE** — premium Telegram panel: live jamoa, reys, QR zonalar, yakuniy hisobot.

Ma'lumotlar hozircha **RAM**da (PostgreSQL keyinroq).

## ✨ Ko'rinish

- 🟢 **LIVE** guruh kartasi (har 5 s yangilanadi)
- 🥇 Reyting, progress barlar, professional HTML
- 📦 Reys + QR zonalar
- 📊 Yakuniy hisobot kartasi

## Buyruqlar

| Buyruq | Vazifa |
|--------|--------|
| `/start` | Premium menyu / QR yakunlash |
| `/startmove` | Mas'ul — jarayon boshlash |
| `/zones` | QR havolalar |
| `/id` | Chat ID |
| `/cancel` | Yakunlash suratlarini bekor qilish |

## Guruh

`✅ Qatnashish` · `📦 Reys oldim` · `🏁 Yakunlash`

## Railway

```
BOT_TOKEN=...
GROUP_ID=-100...
ADMIN_IDS=123456789
TICK_SEC=5
```

Bot **guruhda admin** bo'lishi kerak.

## Ishga tushirish

```bash
pip install -r requirements.txt
cp env.example .env
python bot.py
```
