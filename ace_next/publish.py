from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import AceNextConfig


@dataclass
class PublishReceipt:
    ok: bool
    publish_status: str
    created_at: str
    content_type: str
    trend: str | None = None
    style: str | None = None
    caption: str | None = None
    media_path: str | None = None
    media_url: str | None = None
    raw_publish_result: dict[str, Any] | None = None
    error: str | None = None


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

    def save_receipt(self, receipt: PublishReceipt) -> dict[str, Any]:
        payload = asdict(receipt)
        self.receipt_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    def save_error(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.error_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
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

    def publish_placeholder(
        self,
        *,
        trend: str,
        style: str,
        content_type: str,
        caption: str,
        media_path: str | None,
    ) -> dict[str, Any]:
        media_url = self.build_media_url(media_path)
        receipt = PublishReceipt(
            ok=False if not self.config.enable_real_publish else True,
            publish_status="generated" if not self.config.enable_real_publish else "published",
            created_at=datetime.now().isoformat(),
            content_type=content_type,
            trend=trend,
            style=style,
            caption=caption,
            media_path=media_path,
            media_url=media_url,
            raw_publish_result={
                "mode": "placeholder",
                "real_publish_enabled": self.config.enable_real_publish,
            },
            error=None if self.config.enable_real_publish else "real_publish_disabled",
        )

        saved = self.save_receipt(receipt)
        if not receipt.ok:
            self.save_error(saved)
        return saved
