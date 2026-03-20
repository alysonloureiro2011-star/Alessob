from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import AceNextConfig

AUTH_FILENAME = "instagram_auth.json"
TOKEN_ENV_KEYS = ("IG_TOKEN", "IG_ACCESS_TOKEN", "INSTAGRAM_TOKEN")
USER_ENV_KEYS = ("IG_ID", "IG_USER_ID")


def auth_path(config: AceNextConfig) -> Path:
    configured = os.environ.get("ACE_INSTAGRAM_AUTH_PATH")
    if configured:
        return Path(configured)
    return getattr(config, "auth_path", config.base_dir / AUTH_FILENAME)


def _safe_read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def token_preview(token: str | None) -> str | None:
    if not token:
        return None
    return token if len(token) <= 12 else f"{token[:12]}..."


def save_instagram_auth(
    config: AceNextConfig,
    *,
    token: str | None = None,
    user_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path = auth_path(config)
    existing = _safe_read_json(path)
    existing_meta = existing.get("meta") if isinstance(existing.get("meta"), dict) else {}

    merged_meta = dict(existing_meta)
    if isinstance(meta, dict):
        merged_meta.update(meta)

    payload = {
        "token": token or config.ig_token,
        "user_id": str(user_id or config.ig_id) if (user_id or config.ig_id) else None,
        "saved_at": datetime.now().isoformat(),
        "meta": merged_meta,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def load_instagram_auth(config: AceNextConfig) -> dict[str, Any]:
    return _safe_read_json(auth_path(config))


def _first_present(values: list[str | None]) -> str | None:
    for value in values:
        if value:
            return str(value)
    return None


def _first_present_with_source(
    values: list[tuple[str, str | None]],
) -> tuple[str | None, str | None]:
    for source, value in values:
        if value:
            return str(value), source
    return None, None


def reset_instagram_auth(config: AceNextConfig) -> dict[str, Any]:
    path = auth_path(config)
    deleted = False
    if path.exists():
        path.unlink()
        deleted = True
    return {
        "ok": True,
        "deleted": deleted,
        "auth_path": str(path),
    }


def sync_instagram_token_sources(
    config: AceNextConfig,
    *,
    runtime_token: str | None = None,
    runtime_user_id: str | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    stored = load_instagram_auth(config)

    unified_token, token_source = _first_present_with_source(
        [
            ("env:IG_TOKEN", os.environ.get("IG_TOKEN")),
            ("env:IG_ACCESS_TOKEN", os.environ.get("IG_ACCESS_TOKEN")),
            ("env:INSTAGRAM_TOKEN", os.environ.get("INSTAGRAM_TOKEN")),
            ("config.ig_token", config.ig_token),
            ("runtime", runtime_token),
            ("json", stored.get("token")),
        ]
    )

    unified_user_id, user_id_source = _first_present_with_source(
        [
            ("env:IG_ID", os.environ.get("IG_ID")),
            ("env:IG_USER_ID", os.environ.get("IG_USER_ID")),
            ("config.ig_id", config.ig_id),
            ("runtime", runtime_user_id),
            ("json:user_id", stored.get("user_id")),
            ("json:ig_id", stored.get("ig_id")),
        ]
    )

    if unified_token:
        for key in TOKEN_ENV_KEYS:
            os.environ[key] = unified_token
        object.__setattr__(config, "ig_token", unified_token)

    if unified_user_id:
        for key in USER_ENV_KEYS:
            os.environ[key] = unified_user_id
        object.__setattr__(config, "ig_id", unified_user_id)

    payload = None
    if persist and (unified_token or unified_user_id):
        payload = save_instagram_auth(
            config,
            token=unified_token,
            user_id=unified_user_id,
            meta={
                "source": token_source or "ace_sync_ig_token_sources",
                "user_id_source": user_id_source,
                "last_synced_at": datetime.now().isoformat(),
            },
        )

    meta = payload.get("meta") if isinstance(payload, dict) else (stored.get("meta") or {})

    return {
        "ok": True,
        "token_present": bool(unified_token),
        "ig_id_present": bool(unified_user_id),
        "token_preview": token_preview(unified_token),
        "token_source": token_source,
        "ig_user_id": unified_user_id,
        "user_id_source": user_id_source,
        "auth_path": str(auth_path(config)),
        "persisted": bool(payload),
        "saved_at": payload.get("saved_at") if isinstance(payload, dict) else stored.get("saved_at"),
        "expires_at": meta.get("expires_at") if isinstance(meta, dict) else None,
        "refreshed_at": meta.get("refreshed_at") if isinstance(meta, dict) else None,
    }
