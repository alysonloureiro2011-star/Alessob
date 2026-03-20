from __future__ import annotations

import requests

from .auth_store import save_instagram_auth
from .config import AceNextConfig


def exchange_code_for_token_with_redirect(
    config: AceNextConfig,
    *,
    code: str,
    redirect_uri: str,
    timeout: int = 30,
) -> dict[str, object]:
    if not config.instagram_app_id or not config.instagram_app_secret:
        return {"ok": False, "error": "INSTAGRAM_APP_ID ou INSTAGRAM_APP_SECRET ausentes"}

    data = {
        "client_id": config.instagram_app_id,
        "client_secret": config.instagram_app_secret,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
        "code": code,
    }

    try:
        response = requests.post(
            "https://api.instagram.com/oauth/access_token",
            data=data,
            timeout=timeout,
        )
        try:
            body = response.json()
        except Exception:
            body = {"raw": response.text[:1000]}
        if response.status_code >= 400:
            return {"ok": False, "status": response.status_code, "error": body}

        access_token = body.get("access_token")
        user_id = body.get("user_id")
        if access_token:
            save_instagram_auth(
                config,
                token=access_token,
                user_id=str(user_id) if user_id else None,
                meta={"source": "callback_code_exchange", "redirect_uri": redirect_uri},
            )
        return {"ok": True, "data": body}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def exchange_instagram_long_lived_token(
    config: AceNextConfig,
    *,
    current_token: str,
    current_user_id: str | None,
    timeout: int = 30,
) -> dict[str, object]:
    if not current_token:
        return {"ok": False, "error": "IG_TOKEN ausente"}
    if not config.instagram_app_secret:
        return {"ok": False, "error": "INSTAGRAM_APP_SECRET ausente"}

    params = {
        "grant_type": "ig_exchange_token",
        "client_secret": config.instagram_app_secret,
        "access_token": current_token,
    }
    try:
        response = requests.get(
            "https://graph.instagram.com/access_token",
            params=params,
            timeout=timeout,
        )
        try:
            body = response.json()
        except Exception:
            body = {"raw": response.text[:1000]}
        if response.status_code >= 400:
            return {"ok": False, "status_code": response.status_code, "error": body}

        new_token = body.get("access_token")
        if new_token:
            save_instagram_auth(
                config,
                token=new_token,
                user_id=current_user_id,
                meta={"source": "long_lived_exchange"},
            )
        return {"ok": True, "data": body}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def upgrade_token_via_facebook_exchange(
    config: AceNextConfig,
    *,
    short_token: str,
    current_user_id: str | None,
    timeout: int = 20,
) -> dict[str, object]:
    app_id = config.instagram_app_id
    app_secret = config.instagram_app_secret
    if not app_id or not app_secret:
        return {"ok": False, "error": "APP_ID ou APP_SECRET ausente"}
    if not short_token:
        return {"ok": False, "error": "IG_TOKEN não encontrado"}

    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_token,
    }
    try:
        response = requests.get(
            "https://graph.facebook.com/v19.0/oauth/access_token",
            params=params,
            timeout=timeout,
        )
        try:
            body = response.json()
        except Exception:
            body = {"raw": response.text[:1000]}
        if response.status_code >= 400:
            return {"ok": False, "status_code": response.status_code, "error": body}

        long_token = body.get("access_token")
        if long_token:
            save_instagram_auth(
                config,
                token=long_token,
                user_id=current_user_id,
                meta={"source": "token_upgrade"},
            )
            return {
                "ok": True,
                "token": long_token,
                "expires_in": body.get("expires_in"),
                "data": body,
            }
        return {"ok": False, "data": body}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
