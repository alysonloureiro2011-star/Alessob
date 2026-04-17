from __future__ import annotations

import os
from typing import Any


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


class YouTubeAdapter:
    platform = "youtube"

    def __init__(self, config: Any | None = None) -> None:
        self.config = config

    def status(self) -> dict[str, Any]:
        credentials = {
            "client_id": bool(os.environ.get("YOUTUBE_CLIENT_ID")),
            "client_secret": bool(os.environ.get("YOUTUBE_CLIENT_SECRET")),
            "refresh_token": bool(os.environ.get("YOUTUBE_REFRESH_TOKEN")),
            "channel_id": bool(os.environ.get("YOUTUBE_CHANNEL_ID")),
        }
        configured = all(credentials.values())
        return {
            "ok": True,
            "platform": self.platform,
            "adapter_state": "configured" if configured else "stub_not_configured",
            "can_publish": configured,
            "credentials_present": credentials,
        }

    def build_publish_payload(
        self,
        *,
        caption: str = "",
        media_path: str | None = None,
        metadata: dict[str, Any] | None = None,
        linkage_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        metadata = dict(metadata or {})
        linkage_context = dict(linkage_context or {})

        title = _clean_text(
            metadata.get("title")
            or metadata.get("headline")
            or caption[:100]
            or "ACE Ω YouTube Upload"
        )

        description = _clean_text(
            metadata.get("description")
            or metadata.get("body")
            or caption
        )

        tags = metadata.get("hashtags") or metadata.get("tags") or []
        if not isinstance(tags, list):
            tags = []

        return {
            "platform": self.platform,
            "title": title[:100],
            "description": description[:5000],
            "tags": [str(tag).strip() for tag in tags if str(tag).strip()][:15],
            "media_path": media_path,
            "privacy_status": metadata.get("privacy_status") or "private",
            "category_id": metadata.get("category_id") or "22",
            "linkage_context": linkage_context,
        }

    def publish(
        self,
        *,
        caption: str = "",
        media_path: str | None = None,
        metadata: dict[str, Any] | None = None,
        dry_run: bool = True,
        linkage_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = self.build_publish_payload(
            caption=caption,
            media_path=media_path,
            metadata=metadata,
            linkage_context=linkage_context,
        )
        status = self.status()

        if dry_run:
            return {
                "ok": True,
                "platform": self.platform,
                "adapter_state": status["adapter_state"],
                "dry_run": True,
                "publish_status": "dry_run_only",
                "receipt_id": None,
                "media_id": None,
                "permalink": None,
                "payload": payload,
                "warnings": ["youtube_adapter_stub"],
                "next_step": "integrate_youtube_api_client",
            }

        if not status["can_publish"]:
            return {
                "ok": False,
                "platform": self.platform,
                "adapter_state": status["adapter_state"],
                "dry_run": False,
                "publish_status": "adapter_not_configured",
                "receipt_id": None,
                "media_id": None,
                "permalink": None,
                "payload": payload,
                "error": "missing_youtube_credentials",
                "next_step": "set YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN and YOUTUBE_CHANNEL_ID",
            }

        return {
            "ok": False,
            "platform": self.platform,
            "adapter_state": "configured_stub",
            "dry_run": False,
            "publish_status": "not_implemented_yet",
            "receipt_id": None,
            "media_id": None,
            "permalink": None,
            "payload": payload,
            "error": "youtube_publish_not_implemented_yet",
            "next_step": "implement_youtube_upload_flow",
        }
