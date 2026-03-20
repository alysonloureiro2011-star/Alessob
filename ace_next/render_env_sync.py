from __future__ import annotations

import os
from typing import Any

import requests

DEFAULT_RENDER_SERVICE_ID = "srv-d6oaf3fafjfc7382eaa0"


def persist_instagram_token_to_render(
    *,
    token: str,
    user_id: str | None = None,
    service_id: str | None = None,
    api_key: str | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    render_api_key = api_key or os.environ.get("ACE_RENDER_API_KEY")
    render_service_id = service_id or os.environ.get("ACE_RENDER_SERVICE_ID") or DEFAULT_RENDER_SERVICE_ID

    if not render_api_key:
        return {
            "ok": False,
            "persisted": False,
            "error": "ACE_RENDER_API_KEY ausente",
            "service_id": render_service_id,
        }

    updates = {
        "IG_TOKEN": token,
        "IG_ACCESS_TOKEN": token,
        "INSTAGRAM_TOKEN": token,
    }

    if user_id:
        updates["IG_ID"] = str(user_id)
        updates["IG_USER_ID"] = str(user_id)

    headers = {
        "Authorization": f"Bearer {render_api_key}",
        "Content-Type": "application/json",
    }

    results: dict[str, Any] = {}
    all_ok = True

    for key, value in updates.items():
        url = f"https://api.render.com/v1/services/{render_service_id}/env-vars/{key}"
        try:
            response = requests.put(
                url,
                headers=headers,
                json={"value": value},
                timeout=timeout,
            )

            try:
                body = response.json()
            except Exception:
                body = {"raw": response.text[:2000]}

            ok = response.status_code < 400
            results[key] = {
                "ok": ok,
                "status_code": response.status_code,
                "body": body,
            }
            if ok:
                os.environ[key] = str(value)
            else:
                all_ok = False
        except Exception as exc:
            results[key] = {
                "ok": False,
                "error": str(exc),
            }
            all_ok = False

    return {
        "ok": all_ok,
        "persisted": all_ok,
        "service_id": render_service_id,
        "updates": results,
    }
