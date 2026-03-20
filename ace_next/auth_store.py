from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import AceNextConfig

AUTH_FILENAME = "instagram_auth.json"

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
    payload = {
        "token": token or config.ig_token,
        "user_id": str(user_id or config.ig_id) if (user_id or config.ig_id) else None,
        "saved_at": datetime.now().isoformat(),
        "meta": meta or {},
    }
    path = auth_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload

def load_instagram_auth(config: AceNextConfig) -> dict[str, Any]:
    return _safe_read_json(auth_path(config))

def sync_instagram_token_sources(
    config: AceNextConfig,
    *,
    runtime_token: str | None = None,
    runtime_user_id: str | None = None,
    persist: bool = True,
) -> dict[str, Any]:

    stored = load_instagram_auth(config)

    # 🔥 PRIORIDADE CORRETA (ENV PRIMEIRO)
    unified_token = (
        os.environ.get("IG_TOKEN")
        or os.environ.get("IG_ACCESS_TOKEN")
        or os.environ.get("INSTAGRAM_TOKEN")
        or runtime_token
        or config.ig_token
        or stored.get("token")
    )

    unified_user_id = (
        os.environ.get("IG_ID")
        or os.environ.get("IG_USER_ID")
        or runtime_user_id
        or config.ig_id
        or stored.get("user_id")
        or stored.get("ig_id")
    )

    if unified_token:
        os.environ["IG_TOKEN"] = unified_token
        os.environ["IG_ACCESS_TOKEN"] = unified_token
        os.environ["INSTAGRAM_TOKEN"] = unified_token
        object.__setattr__(config, "ig_token", unified_token)

    if unified_user_id:
        os.environ["IG_ID"] = unified_user_id
        os.environ["IG_USER_ID"] = unified_user_id
        object.__setattr__(config, "ig_id", unified_user_id)

    payload = None
    if persist and (unified_token or unified_user_id):
        payload = save_instagram_auth(
            config,
            token=unified_token,
            user_id=unified_user_id,
            meta={"source": "ENV_PRIORITY_FIX"},
        )

    return {
        "ok": True,
        "token_preview": token_preview(unified_token),
        "ig_user_id": unified_user_id,
        "auth_path": str(auth_path(config)),
        "persisted": bool(payload),
    }
