from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .official_instagram_publish import OfficialInstagramPublishService


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _normalize_media_paths(
    media_path: str | None,
    linkage_context: dict[str, Any] | None = None,
) -> list[str]:
    linkage_context = _safe_dict(linkage_context)
    raw_paths = linkage_context.get("media_paths")

    normalized: list[str] = []

    if isinstance(raw_paths, list):
        for item in raw_paths:
            text = _clean_text(item)
            if text and text not in normalized:
                normalized.append(text)

    primary = _clean_text(media_path)
    if primary and primary not in normalized:
        normalized.insert(0, primary)

    return normalized


class PublishService:
    def __init__(self, config) -> None:
        self.config = config
        self.publisher = OfficialInstagramPublishService(config)
        self.state_path = Path(config.data_dir) / "ace_next_last_publish.json"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def _default_state(self) -> dict[str, Any]:
        return {
            "ok": True,
            "source_of_truth": "legacy_fallback",
            "latest_media_id": None,
            "latest_permalink": None,
            "latest_evidence_state": None,
            "latest_resolution_state": None,
            "latest_receipt_id": None,
            "latest_publish_status": None,
            "updated_at": None,
            "recent_episodes": [],
        }

    def _read_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return self._default_state()

        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                base = self._default_state()
                base.update(data)
                base["recent_episodes"] = _safe_list(base.get("recent_episodes"))
                return base
        except Exception:
            pass

        return self._default_state()

    def _write_state(self, payload: dict[str, Any]) -> None:
        state = self._read_state()
        state.update(_safe_dict(payload))
        state["updated_at"] = _now_iso()

        recent_episodes = _safe_list(state.get("recent_episodes"))
        episode = {
            "receipt_id": state.get("latest_receipt_id"),
            "publish_status": state.get("latest_publish_status"),
            "media_id": state.get("latest_media_id"),
            "permalink": state.get("latest_permalink"),
            "evidence_state": state.get("latest_evidence_state"),
            "resolution_state": state.get("latest_resolution_state"),
            "updated_at": state.get("updated_at"),
        }

        if (
            episode.get("receipt_id")
            or episode.get("publish_status")
            or episode.get("media_id")
            or episode.get("permalink")
        ):
            recent_episodes.append(episode)
            state["recent_episodes"] = recent_episodes[-20:]
        else:
            state["recent_episodes"] = recent_episodes[-20:]

        self.state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _build_receipt_id(self) -> str:
        return f"ace-{int(datetime.now(timezone.utc).timestamp())}"

    def last_publish(self) -> dict[str, Any]:
        return self._read_state()

    def _record_placeholder(
        self,
        *,
        receipt_id: str,
        publish_status: str,
        resolution_state: str,
    ) -> None:
        self._write_state(
            {
                "source_of_truth": "placeholder",
                "latest_receipt_id": receipt_id,
                "latest_publish_status": publish_status,
                "latest_media_id": None,
                "latest_permalink": None,
                "latest_evidence_state": "placeholder_only",
                "latest_resolution_state": resolution_state,
            }
        )

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
        receipt_id = self._build_receipt_id()

        result = {
            "ok": True,
            "publish_status": "placeholder_recorded",
            "receipt_id": receipt_id,
            "media_id": None,
            "permalink": None,
            "content_type": content_type,
            "style": style,
            "caption": caption,
            "trend": trend,
            "created_at": _now_iso(),
            "linkage_context": _safe_dict(linkage_context),
            "media_path": media_path,
        }

        self._record_placeholder(
            receipt_id=receipt_id,
            publish_status="placeholder_recorded",
            resolution_state="not_published",
        )
        return result

    def _failure_result(
        self,
        *,
        receipt_id: str,
        reason: Any,
        trend: str,
        style: str,
        content_type: str,
        caption: str,
        media_path: str | None,
        linkage_context: dict[str, Any] | None = None,
        publish_status: str = "publish_failed",
    ) -> dict[str, Any]:
        self._write_state(
            {
                "source_of_truth": "real_publish_failed",
                "latest_receipt_id": receipt_id,
                "latest_publish_status": publish_status,
                "latest_media_id": None,
                "latest_permalink": None,
                "latest_evidence_state": "publish_failed",
                "latest_resolution_state": "publish_failed",
            }
        )

        return {
            "ok": False,
            "publish_status": publish_status,
            "error": reason,
            "receipt_id": receipt_id,
            "media_id": None,
            "permalink": None,
            "content_type": content_type,
            "style": style,
            "caption": caption,
            "trend": trend,
            "created_at": _now_iso(),
            "linkage_context": _safe_dict(linkage_context),
            "media_path": media_path,
        }

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
        receipt_id = self._build_receipt_id()
        readiness = self.publisher.readiness()

        if not readiness.get("instagram_connected"):
            return self._failure_result(
                receipt_id=receipt_id,
                reason="instagram_not_connected",
                trend=trend,
                style=style,
                content_type=content_type,
                caption=caption,
                media_path=media_path,
                linkage_context=linkage_context,
            )

        if not media_path:
            return self._failure_result(
                receipt_id=receipt_id,
                reason="media_path_missing",
                trend=trend,
                style=style,
                content_type=content_type,
                caption=caption,
                media_path=media_path,
                linkage_context=linkage_context,
            )

        lowered = str(content_type or "").strip().lower()
        media_paths = _normalize_media_paths(media_path, linkage_context)

        if lowered == "carousel":
            if len(media_paths) < 2:
                return self._failure_result(
                    receipt_id=receipt_id,
                    reason={
                        "reason": "carousel_requires_two_real_media_paths",
                        "media_paths_seen": media_paths,
                    },
                    trend=trend,
                    style=style,
                    content_type=content_type,
                    caption=caption,
                    media_path=media_path,
                    linkage_context=linkage_context,
                    publish_status="carousel_not_ready",
                )

            publish_response = self.publisher.publish_carousel(
                caption=caption,
                media_paths=media_paths,
            )
        else:
            publish_response = self.publisher.publish_single(
                caption=caption,
                media_path=media_path,
                content_type=lowered or "image",
            )

        if not publish_response.get("ok"):
            return self._failure_result(
                receipt_id=receipt_id,
                reason=publish_response,
                trend=trend,
                style=style,
                content_type=content_type,
                caption=caption,
                media_path=media_path,
                linkage_context=linkage_context,
            )

        published_payload = _safe_dict(publish_response.get("published"))
        media_id = published_payload.get("id")
        permalink = None

        if media_id:
            permalink_lookup = self.publisher.instagram_request(
                "GET",
                f"{media_id}",
                params={"fields": "permalink"},
                timeout=60,
            )
            if permalink_lookup.get("ok"):
                permalink = _safe_dict(permalink_lookup.get("data")).get("permalink")

        result = {
            "ok": True,
            "publish_status": "published_real_probe",
            "receipt_id": receipt_id,
            "media_id": media_id,
            "permalink": permalink,
            "content_type": content_type,
            "style": style,
            "caption": caption,
            "trend": trend,
            "created_at": _now_iso(),
            "linkage_context": _safe_dict(linkage_context),
            "media_path": media_path,
            "media_paths": media_paths,
            "provider_result": publish_response,
        }

        self._write_state(
            {
                "source_of_truth": "real_publish",
                "latest_receipt_id": receipt_id,
                "latest_publish_status": "published_real_probe",
                "latest_media_id": media_id,
                "latest_permalink": permalink,
                "latest_evidence_state": "linked_real_target" if media_id else "publish_attempt_recorded",
                "latest_resolution_state": "collecting",
            }
        )
        return result

    def publish(
        self,
        *,
        trend: str,
        style: str,
        content_type: str,
        caption: str,
        media_path: str | None,
        linkage_context: dict[str, Any] | None = None,
        real: bool = False,
    ) -> dict[str, Any]:
        if real:
            return self.publish_real(
                trend=trend,
                style=style,
                content_type=content_type,
                caption=caption,
                media_path=media_path,
                linkage_context=linkage_context,
            )
        return self.publish_placeholder(
            trend=trend,
            style=style,
            content_type=content_type,
            caption=caption,
            media_path=media_path,
            linkage_context=linkage_context,
        )
