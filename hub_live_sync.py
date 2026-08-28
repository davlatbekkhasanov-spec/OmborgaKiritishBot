"""Jonli hub sessiyalarini RAM holati bilan moslashtirish."""

from __future__ import annotations

import json
import logging
import urllib.request

import storage
from yordamchi_push import HUB_SECRET, HUB_URL, push_session_end_background

log = logging.getLogger(__name__)


def reconcile_hub_live_sessions() -> None:
    active_ids = {int(s.get("user_id") or 0) for s in storage.active_users()}
    active_ids.discard(0)
    if not HUB_URL or not HUB_SECRET:
        return
    try:
        req = urllib.request.Request(
            f"{HUB_URL.rstrip('/')}/api/live",
            headers={"Accept": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for sess in data.get("sessions") or []:
            if str(sess.get("bot_key") or "") != "omborga":
                continue
            uid = int(sess.get("tg_id") or 0)
            if uid and uid not in active_ids:
                push_session_end_background(tg_id=uid, bot_key="omborga", activity_type="omborga")
                log.info("Hub live reconcile: omborga sessiya yopildi tg=%s", uid)
    except Exception as e:
        log.debug("omborga hub reconcile: %s", e)
