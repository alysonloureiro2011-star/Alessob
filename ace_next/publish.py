from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import AceNextConfig

try:
    from ace.engines.episodic_memory_engine import (
        build_memory_summary as episodic_build_memory_summary,
        set_last_publish_error as episodic_set_last_publish_error,
        set_last_publish_receipt as episodic_set_last_publish_receipt,
    )
except Exception:
    episodic_build_memory_summary = None
    episodic_set_last_publish_error = None
    episodic_set_last_publish_receipt = None


@dataclass
class PublishReceipt:
    ok: bool
    publish_status: str
    created_at: str
    content_type: str | None = None
    trend: str | None = None
    style: str | None = None
    caption: str | None = None
    media_path: str | None = None
    media_url: str | None = None
    raw_publish_result: dict[str, Any] | None = None
    error: str | None = None
    creation_id: str | None = None
    media_id: str | None = None
    permalink: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PublishService:
    def __init__(self, config: AceNextConfig) -> None:
        self.config = config
        self.receipt_path = config.data_dir / "ace_next_publish_receipt.json"
        self.error_path = config.data_dir / "ace_next_publish_error.json"

    def build_media_url(self, media_path: str | None) -> str | None:
        if not media_path:
            return None
        name = Path(media_path).name
        if not name:
            return None
        return f"{self.config.public_media_base_url.rstrip('/')}/media/{name}"

    def _normalize_payload(
        self,
        payload: PublishReceipt | dict[str, Any],
    ) -> dict[str, Any]:
        if isinstance(payload, PublishReceipt):
            return payload.to_dict()
        return dict(payload or {})

    def save_receipt(
        self,
        receipt: PublishReceipt | dict[str, Any],
    ) -> dict[str, Any]:
        payload = self._normalize_payload(receipt)
        self.receipt_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if callable(episodic_set_last_publish_receipt):
            try:
                episodic_set_last_publish_receipt(payload)
            except Exception:
                pass
        return payload

    def save_error(
        self,
        error: PublishReceipt | dict[str, Any],
    ) -> dict[str, Any]:
        payload = self._normalize_payload(error)
        self.error_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if callable(episodic_set_last_publish_error):
            try:
                episodic_set_last_publish_error(payload)
            except Exception:
                pass
        return payload

    def get_last_receipt(self) -> dict[str, Any] | None:
        if not self.receipt_path.exists():
            return None
        try:
            return json.loads(self.receipt_path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def get_last_error(self) -> dict[str, Any] | None:
        if not self.error_path.exists():
            return None
        try:
            return json.loads(self.error_path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def last_publish(self) -> dict[str, Any]:
        if callable(episodic_build_memory_summary):
            try:
                summary = episodic_build_memory_summary()
                if isinstance(summary, dict):
                    return summary
            except Exception:
                pass

        return {
            "ok": True,
            "last_publish_receipt": self.get_last_receipt(),
            "last_publish_error": self.get_last_error(),
            "last_episode": None,
        }

    def publish_placeholder(
        self,
        *,
        trend: str,
        style: str,
        content_type: str,
        caption: str,
        media_path: str | None,
    ) -> dict[str, Any]:
        receipt = build_placeholder_receipt(
            created_at=datetime.now().isoformat(),
            content_type=content_type,
            trend=trend,
            style=style,
            caption=caption,
            media_path=media_path,
            media_url=self.build_media_url(media_path),
            raw_publish_result={
                "mode": "placeholder",
                "real_publish_enabled": self.config.enable_real_publish,
            },
            error="placeholder_mode",
        )
        saved = self.save_receipt(receipt)
        self.save_error(receipt)
        return saved


def build_placeholder_receipt(**kwargs: Any) -> PublishReceipt:
    created_at = kwargs.get("created_at") or datetime.utcnow().isoformat()
    return PublishReceipt(
        ok=bool(kwargs.get("ok", False)),
        publish_status=kwargs.get("publish_status") or "placeholder",
        created_at=created_at,
        content_type=kwargs.get("content_type"),
        trend=kwargs.get("trend"),
        style=kwargs.get("style"),
        caption=kwargs.get("caption"),
        media_path=kwargs.get("media_path"),
        media_url=kwargs.get("media_url"),
        raw_publish_result=kwargs.get("raw_publish_result"),
        error=kwargs.get("error") or "publish_placeholder_fallback",
        creation_id=kwargs.get("creation_id"),
        media_id=kwargs.get("media_id"),
        permalink=kwargs.get("permalink"),
    )
