# Omborga Kiritish Bot

Mashina yuk tushgandan keyin omborga olib kirish jarayonini nazorat qiladi.

## 1-bosqich (hozir)

Ma'lumotlar **RAM**da (redeployda yo'qoladi). PostgreSQL keyinroq ulanadi.

## Buyruqlar

| Buyruq | Kim | Vazifa |
|--------|-----|--------|
| `/start` | Hamma | Yordam; `zone_OMBOR_A` — QR yakunlash |
| `/id` | Hamma | Chat ID |
| `/startmove` | Mas'ul/admin | Jarayonni boshlash, guruhga xabar |
| `/zones` | Hamma | QR havolalar ro'yxati |
| `/cancel` | Mas'ul | Yakunlash fotosuratlarini bekor qilish |

## Guruh tugmalari

- **Qatnashish** — ishchi ro'yxatga (bir marta)
- **Reys oldim** — reys boshlanadi, keyin zonada QR
- **Yakunlash** — faqat mas'ul/admin (2 ta rasm, final hisobot)

## QR zonalar

- `OMBOR_A` — 12 m
- `OMBOR_B` — 24 m
- `SOVUQ_XONA` — 41 m

Namuna: `https://t.me/BOT_USERNAME?start=zone_OMBOR_A`

## Railway

```
BOT_TOKEN=...
GROUP_ID=-100...
ADMIN_IDS=123456789
```

Bot guruhda **admin** bo'lishi kerak (xabarni tahrirlash).

## Ishga tushirish

```bash
pip install -r requirements.txt
cp env.example .env
python bot.py
```
