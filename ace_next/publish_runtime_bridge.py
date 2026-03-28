from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from .config import AceNextConfig
from .official_instagram_publish import OfficialInstagramPublishService
from .publish import (
    ALLOWED_REAL_PROBE_STATES,
    PublishReceipt,
    PublishService as LegacyPublishService,
    _probe_payload,
)


class PublishService:
    def __init__(self, config: AceNextConfig) -> None:
        self.config = config
        self.legacy = LegacyPublishService(config)
        self.instagram = OfficialInstagramPublishService(config)

    def build_media_url(self, media_path: str | None) -> str | None:
        return self.instagram.media_public_url_from_path(media_path)

    def save_receipt(self, receipt: PublishReceipt | dict[str, Any]) -> dict[str, Any]:
        return self.legacy.save_receipt(receipt)

    def save_error(self, error: PublishReceipt | dict[str, Any]) -> dict[str, Any]:
        return self.legacy.save_error(error)

    def get_last_receipt(self) -> dict[str, Any] | None:
        return self.legacy.get_last_receipt()

    def get_last_error(self) -> dict[str, Any] | None:
        return self.legacy.get_last_error()

    def last_publish(self) -> dict[str, Any]:
        return self.legacy.last_publish()

    def publish_placeholder(
        self,
        *,
        trend: str,
        style: str,
        content_type: str,
        caption: str,
        media_path: str | None,
        linkage_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.legacy.publish_placeholder(
            trend=trend,
            style=style,
            content_type=content_type,
            caption=caption,
            media_path=media_path,
            linkage_context=linkage_context,
        )

    def _normalize_content_type(self, content_type: str | None) -> str:
        value = str(content_type or "image").strip().lower()
        if value in {"carrossel", "carousel"}:
            return "carousel"
        if value in {"reel", "video", "image", "story"}:
            return value
        return "image"

    def _error(
        self,
        *,
        content_type: str,
        trend: str,
        style: str,
        caption: str,
        media_path: str | None,
        linkage_context: dict[str, Any] | None,
        error: str,
        raw_publish_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.legacy._build_error_receipt(
            content_type=content_type,
            trend=trend,
            style=style,
            caption=caption,
            media_path=media_path,
            media_url=self.build_media_url(media_path),
            linkage_context=linkage_context,
            error=error,
            raw_publish_result=raw_publish_result,
        )

    def publish_real(
        self,
        *,
        trend: str,
        style: str,
        content_type: str,
        caption: str,
        media_path: str | None,
        linkage_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        probe = _probe_payload(linkage_context)
        probe_requested = bool(probe.get("requested"))
        effective_state = str(probe.get("effective_state") or "").strip().lower()
        allow_real_publish = bool(probe.get("allow_real_publish"))

        if not probe_requested:
            return self._error(
                content_type=content_type,
                trend=trend,
                style=style,
                caption=caption,
                media_path=media_path,
                linkage_context=linkage_context,
                error="real_publish_without_probe_not_allowed",
                raw_publish_result={"probe": probe},
            )

        if not allow_real_publish or effective_state not in ALLOWED_REAL_PROBE_STATES:
            return self._error(
                content_type=content_type,
                trend=trend,
                style=style,
                caption=caption,
                media_path=media_path,
                linkage_context=linkage_context,
                error="real_probe_blocked_by_guardrail",
                raw_publish_result={"probe": probe},
            )

        if not self.config.enable_real_publish:
            return self.publish_placeholder(
                trend=trend,
                style=style,
                content_type=content_type,
                caption=caption,
                media_path=media_path,
                linkage_context=linkage_context,
            )

        normalized = self._normalize_content_type(content_type)

        if normalized == "carousel":
            raw_paths = list((linkage_context or {}).get("carousel_media_paths") or [])
            media_paths = [str(item).strip() for item in raw_paths if str(item).strip()]
            if len(media_paths) < 2:
                return self._error(
                    content_type=content_type,
                    trend=trend,
                    style=style,
                    caption=caption,
                    media_path=media_path,
                    linkage_context=linkage_context,
                    error="carousel_media_paths_ausente",
                    raw_publish_result={"probe": probe, "carousel_media_paths": media_paths},
                )
            result = self.instagram.publish_carousel(caption=caption, media_paths=media_paths)
            if not result.get("ok"):
                return self._error(
                    content_type=content_type,
                    trend=trend,
                    style=style,
                    caption=caption,
                    media_path=media_path,
                    linkage_context=linkage_context,
                    error="carousel_publish_fail",
                    raw_publish_result=result,
                )
            creation_id = (result.get("parent") or {}).get("id")
            media_id = (result.get("published") or {}).get("id")
            info = self.instagram.instagram_request("GET", str(media_id), params={"fields": "id,permalink"}) if media_id else None
            permalink = ((info or {}).get("data") or {}).get("permalink")
        else:
            result = self.instagram.publish_single(
                caption=caption,
                media_path=media_path,
                content_type="reel" if normalized == "reel" else normalized,
            )
            if not result.get("ok"):
                return self._error(
                    content_type=content_type,
                    trend=trend,
                    style=style,
                    caption=caption,
                    media_path=media_path,
                    linkage_context=linkage_context,
                    error="single_publish_fail",
                    raw_publish_result=result,
                )
            creation_id = (result.get("container") or {}).get("id")
            media_id = (result.get("published") or {}).get("id")
            info = self.instagram.instagram_request("GET", str(media_id), params={"fields": "id,permalink"}) if media_id else None
            permalink = ((info or {}).get("data") or {}).get("permalink")

        receipt = PublishReceipt(
            ok=True,
            publish_status="published_real_probe",
            created_at=datetime.now().isoformat(),
            receipt_id=f"receipt_{uuid.uuid4().hex}",
            content_type=content_type,
            trend=trend,
            style=style,
            caption=caption,
            media_path=media_path,
            media_url=self.build_media_url(media_path),
            linkage_context=linkage_context,
            raw_publish_result={"publish_result": result, "info": info, "probe": probe},
            error=None,
            creation_id=creation_id,
            media_id=media_id,
            permalink=permalink,
            operational_state=(linkage_context or {}).get("operational_state"),
            real_probe_requested=True,
            real_probe_executed=True,
            probe_state_requested=probe.get("requested_state"),
            probe_state_effective=probe.get("effective_state"),
        )
        return self.save_receipt(receipt)
