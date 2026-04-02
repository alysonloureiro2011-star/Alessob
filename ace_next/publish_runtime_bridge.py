from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .official_instagram_publish import OfficialInstagramPublishService


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


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
                if not isinstance(base.get("recent_episodes"), list):
                    base["recent_episodes"] = []
                return base
        except Exception:
            pass

        return self._default_state()

    def _write_state(self, payload: dict[str, Any]) -> None:
        state = self._read_state()
        state.update(payload)
        state["updated_at"] = _now_iso()

        recent_episodes = state.get("recent_episodes") or []
        if not isinstance(recent_episodes, list):
            recent_episodes = []

        episode = {
            "media_id": state.get("latest_media_id"),
            "permalink": state.get("latest_permalink"),
            "evidence_state": state.get("latest_evidence_state"),
            "resolution_state": state.get("latest_resolution_state"),
            "updated_at": state.get("updated_at"),
        }

        if episode["media_id"] or episode["permalink"] or episode["evidence_state"]:
            recent_episodes.append(episode)
            state["recent_episodes"] = recent_episodes[-20:]

        self.state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def last_publish(self) -> dict[str, Any]:
        return self._read_state()

    def _build_receipt_id(self) -> str:
        return f"ace-{int(datetime.now(timezone.utc).timestamp())}"

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

        self._write_state(
            {
                "source_of_truth": "placeholder",
                "latest_media_id": None,
                "latest_permalink": None,
                "latest_evidence_state": "placeholder_only",
                "latest_resolution_state": "not_published",
            }
        )
        return result

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
            result = {
                "ok": False,
                "publish_status": "publish_failed",
                "error": "instagram_not_connected",
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
            self._write_state(
                {
                    "source_of_truth": "real_publish_failed",
                    "latest_media_id": None,
                    "latest_permalink": None,
                    "latest_evidence_state": "publish_failed",
                    "latest_resolution_state": "publish_failed",
                }
            )
            return result

        if not media_path:
            result = {
                "ok": False,
                "publish_status": "publish_failed",
                "error": "media_path_missing",
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
            self._write_state(
                {
                    "source_of_truth": "real_publish_failed",
                    "latest_media_id": None,
                    "latest_permalink": None,
                    "latest_evidence_state": "publish_failed",
                    "latest_resolution_state": "publish_failed",
                }
            )
            return result

        lowered = str(content_type or "").strip().lower()

        if lowered == "carousel":
            publish_response = self.publisher.publish_carousel(
                caption=caption,
                media_paths=[media_path, media_path],
            )
        else:
            publish_response = self.publisher.publish_single(
                caption=caption,
                media_path=media_path,
                content_type=lowered or "image",
            )

        if not publish_response.get("ok"):
            result = {
                "ok": False,
                "publish_status": "publish_failed",
                "error": publish_response,
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
            self._write_state(
                {
                    "source_of_truth": "real_publish_failed",
                    "latest_media_id": None,
                    "latest_permalink": None,
                    "latest_evidence_state": "publish_failed",
                    "latest_resolution_state": "publish_failed",
                }
            )
            return result

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
            "provider_result": publish_response,
        }

        self._write_state(
            {
                "source_of_truth": "real_publish",
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
