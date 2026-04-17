from __future__ import annotations

import os
from typing import Any


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


class ThreadsAdapter:
    platform = "threads"

    def __init__(self, config: Any | None = None) -> None:
        self.config = config

    def status(self) -> dict[str, Any]:
        credentials = {
            "access_token": bool(os.environ.get("THREADS_ACCESS_TOKEN")),
            "user_id": bool(os.environ.get("THREADS_USER_ID")),
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

        text = _clean_text(
            metadata.get("text")
            or metadata.get("caption")
            or metadata.get("headline")
            or caption
            or "ACE Ω Threads Post"
        )

        return {
            "platform": self.platform,
            "text": text[:500],
            "media_path": media_path,
            "reply_control": metadata.get("reply_control") or "everyone",
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
                "warnings": ["threads_adapter_stub"],
                "next_step": "integrate_threads_api_client",
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
                "error": "missing_threads_credentials",
                "next_step": "set THREADS_ACCESS_TOKEN and THREADS_USER_ID",
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
            "error": "threads_publish_not_implemented_yet",
            "next_step": "implement_threads_publish_flow",
        }
