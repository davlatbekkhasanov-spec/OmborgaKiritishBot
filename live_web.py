"""HTTP: Ombor LIVE MVP dashboard."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from aiohttp import web

from live_api import build_live_snapshot, live_token_ok

log = logging.getLogger(__name__)
_ASSETS = Path(__file__).resolve().parent / "assets" / "live"


def _token_from_request(request: web.Request) -> str:
    return (request.query.get("token") or request.headers.get("X-Live-Token") or "").strip()


async def handle_health(_request: web.Request) -> web.Response:
    return web.json_response({"ok": True, "service": "omborga-live"})


async def handle_live_api(request: web.Request) -> web.Response:
    token = _token_from_request(request)
    if not live_token_ok(token):
        return web.json_response({"ok": False, "message": "unauthorized"}, status=401)
    try:
        data = build_live_snapshot()
        return web.Response(
            text=json.dumps(data, ensure_ascii=False),
            content_type="application/json",
            charset="utf-8",
        )
    except Exception as e:
        log.exception("live api")
        return web.json_response({"ok": False, "message": str(e)}, status=500)


async def handle_live_page(request: web.Request) -> web.Response:
    token = _token_from_request(request)
    if not live_token_ok(token):
        return web.Response(text="401 — token kerak", status=401, charset="utf-8")
    html_path = _ASSETS / "index.html"
    html = html_path.read_text(encoding="utf-8")
    return web.Response(text=html, content_type="text/html", charset="utf-8")


def register_live_routes(app: web.Application) -> None:
    app.router.add_get("/health", handle_health)
    app.router.add_get("/live", handle_live_page)
    app.router.add_get("/live/api", handle_live_api)


async def start_live_server() -> web.AppRunner | None:
    import os

    port = int(os.getenv("PORT", os.getenv("LIVE_PORT", "8080")) or 8080)
    app = web.Application()
    register_live_routes(app)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info("HTTP :%s — /health /live /live/api", port)
    return runner
