from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from .auth_store import save_instagram_auth
from .config import AceNextConfig

TOKEN_ENV_KEYS = ("IG_TOKEN", "IG_ACCESS_TOKEN", "INSTAGRAM_TOKEN")
USER_ENV_KEYS = ("IG_ID", "IG_USER_ID")


def _expires_at_from_seconds(expires_in: int | None) -> str | None:
    if not expires_in:
        return None
    return (datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))).isoformat()


def _apply_runtime_token(
    config: AceNextConfig,
    *,
    token: str | None,
    user_id: str | None,
) -> None:
    if token:
        for key in TOKEN_ENV_KEYS:
            os.environ[key] = token
        object.__setattr__(config, "ig_token", token)

    if user_id:
        for key in USER_ENV_KEYS:
            os.environ[key] = str(user_id)
        object.__setattr__(config, "ig_id", str(user_id))


def _save_token_payload(
    config: AceNextConfig,
    *,
    token: str | None,
    user_id: str | None,
    source: str,
    expires_in: int | None = None,
    extra_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "source": source,
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
    }
    if expires_in:
        meta["expires_in"] = int(expires_in)
        meta["expires_at"] = _expires_at_from_seconds(int(expires_in))
    if isinstance(extra_meta, dict):
        meta.update(extra_meta)

    payload = save_instagram_auth(
        config,
        token=token,
        user_id=user_id,
        meta=meta,
    )
    _apply_runtime_token(config, token=token, user_id=user_id)
    return payload


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
            _save_token_payload(
                config,
                token=access_token,
                user_id=str(user_id) if user_id else None,
                source="callback_code_exchange",
                expires_in=body.get("expires_in"),
                extra_meta={"redirect_uri": redirect_uri},
            )
        return {"ok": True, "data": body, "token": access_token, "user_id": user_id}
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
        expires_in = body.get("expires_in")
        if new_token:
            _save_token_payload(
                config,
                token=new_token,
                user_id=current_user_id,
                source="long_lived_exchange",
                expires_in=expires_in,
            )
        return {"ok": True, "data": body, "token": new_token, "expires_in": expires_in}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def refresh_instagram_long_lived_token(
    config: AceNextConfig,
    *,
    current_token: str,
    current_user_id: str | None,
    timeout: int = 30,
) -> dict[str, object]:
    if not current_token:
        return {"ok": False, "error": "IG_TOKEN ausente"}

    params = {
        "grant_type": "ig_refresh_token",
        "access_token": current_token,
    }
    try:
        response = requests.get(
            "https://graph.instagram.com/refresh_access_token",
            params=params,
            timeout=timeout,
        )
        try:
            body = response.json()
        except Exception:
            body = {"raw": response.text[:1000]}
        if response.status_code >= 400:
            return {"ok": False, "status_code": response.status_code, "error": body}

        refreshed_token = body.get("access_token") or current_token
        expires_in = body.get("expires_in")
        if refreshed_token:
            _save_token_payload(
                config,
                token=refreshed_token,
                user_id=current_user_id,
                source="long_lived_refresh",
                expires_in=expires_in,
            )
        return {
            "ok": True,
            "data": body,
            "token": refreshed_token,
            "expires_in": expires_in,
        }
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
        expires_in = body.get("expires_in")
        if long_token:
            _save_token_payload(
                config,
                token=long_token,
                user_id=current_user_id,
                source="token_upgrade",
                expires_in=expires_in,
            )
            return {
                "ok": True,
                "token": long_token,
                "expires_in": expires_in,
                "data": body,
            }
        return {"ok": False, "data": body}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
