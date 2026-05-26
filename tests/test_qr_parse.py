"""Deep link / NFC matn ajratish."""

from qr_parse import parse_reys_from_text, parse_zone_from_text
from zones_config import bot_app_deep_link, bot_web_deep_link, zone_deep_link


def test_zone_https():
    url = zone_deep_link("OmborgaKiritishBot", "SKLAD_1")
    assert url.startswith("https://t.me/")
    assert parse_zone_from_text(url) == "SKLAD_1"


def test_zone_tg():
    url = bot_app_deep_link("OmborgaKiritishBot", "zone_SKLAD_1")
    assert url.startswith("tg://")
    assert parse_zone_from_text(url) == "SKLAD_1"


def test_zone_payload_only():
    assert parse_zone_from_text("zone_SKLAD_2") == "SKLAD_2"


def test_reys_variants():
    assert parse_reys_from_text("reys")
    assert parse_reys_from_text(bot_app_deep_link("OmborgaKiritishBot", "reys"))
    assert parse_reys_from_text(bot_web_deep_link("OmborgaKiritishBot", "reys"))
    assert not parse_reys_from_text("zone_SKLAD_1")
