#!/usr/bin/env python3
"""
QR stikerlar — chop etish uchun PNG + HTML.

Ishlatish:
  pip install qrcode[pil] pillow
  python scripts/generate_zone_qr.py --bot SIZNING_BOT_USERNAME

Chiqish: qr_print/*.png va qr_print/chop_etish.html
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from zones_config import ZONES, zone_deep_link


def make_qr_image(url: str, title: str, subtitle: str, out_path: Path) -> None:
    import qrcode
    from PIL import Image, ImageDraw, ImageFont

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qw, qh = qr_img.size

    pad = 24
    text_h = 100
    canvas = Image.new("RGB", (qw + pad * 2, qh + text_h + pad * 2), "white")
    canvas.paste(qr_img, (pad, pad))

    draw = ImageDraw.Draw(canvas)
    try:
        font_l = ImageFont.truetype("arial.ttf", 22)
        font_s = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        font_l = ImageFont.load_default()
        font_s = font_l

    y = qh + pad + 8
    draw.text((pad, y), title, fill="black", font=font_l)
    draw.multiline_text((pad, y + 28), subtitle, fill="#333333", font=font_s, spacing=4)

    canvas.save(out_path, "PNG", optimize=True)


def write_html(bot: str, out_dir: Path) -> None:
    rows = []
    for code, z in ZONES.items():
        url = zone_deep_link(bot, code)
        png = f"{code}.png"
        rows.append(
            f"""
        <div class="card">
          <img src="{png}" alt="{code}" />
          <h3>{z['zone_name']}</h3>
          <p>Gor: {z['horizontal_meter']}m · Ekv: <b>{z['effort_meter']}m</b></p>
          <p class="code">{code}</p>
        </div>"""
        )
    html = f"""<!DOCTYPE html>
<html lang="uz"><head>
<meta charset="utf-8"/>
<title>QR zonalar — {bot}</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 16px; }}
  h1 {{ font-size: 18px; }}
  .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }}
  .card {{ border: 1px solid #ccc; padding: 12px; text-align: center; page-break-inside: avoid; }}
  img {{ max-width: 100%; height: auto; }}
  h3 {{ margin: 8px 0 4px; font-size: 14px; }}
  p {{ margin: 2px 0; font-size: 12px; }}
  .code {{ color: #666; font-size: 11px; }}
  @media print {{ .grid {{ grid-template-columns: repeat(2, 1fr); }} }}
</style>
</head>
<body>
<h1>GLOBUS · OMBOR — QR zonalar (@{bot})</h1>
<p>Brauzerdan <b>Chop etish</b> (Ctrl+P). Har zonaga bitta stiker.</p>
<div class="grid">
{"".join(rows)}
</div>
</body></html>"""
    (out_dir / "chop_etish.html").write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Zona QR PNG generator")
    parser.add_argument(
        "--bot",
        default=(os.getenv("BOT_USERNAME") or "").strip().lstrip("@"),
        help="Bot username (@siz)",
    )
    parser.add_argument(
        "--out",
        default=str(ROOT / "qr_print"),
        help="Chiqish papkasi",
    )
    args = parser.parse_args()
    bot = (args.bot or "").strip().lstrip("@")
    if not bot:
        print("Xato: --bot USERNAME yoki .env da BOT_USERNAME kiriting")
        sys.exit(1)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    urls_file = out_dir / "havolalar.txt"
    lines = [f"Bot: @{bot}\n", f"STAIR_FACTOR={4}\n", "-" * 40 + "\n"]

    for code, z in ZONES.items():
        url = zone_deep_link(bot, code)
        sub = (
            f"Gor: {z['horizontal_meter']}m  Ekv: {z['effort_meter']}m\n"
            f"{url}"
        )
        make_qr_image(url, z["zone_name"], sub, out_dir / f"{code}.png")
        lines.append(f"{z['zone_name']}\n{url}\n\n")
        print(f"OK  {code}  ->  {code}.png")

    urls_file.write_text("".join(lines), encoding="utf-8")
    write_html(bot, out_dir)
    print(f"\nTayyor: {out_dir.resolve()}")
    print("  - har zona: SKLAD_1.png ...")
    print("  - chop_etish.html — brauzerdan chop etish")
    print("  - havolalar.txt — havolalar ro'yxati")


if __name__ == "__main__":
    main()
