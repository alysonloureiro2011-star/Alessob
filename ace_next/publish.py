from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

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
    receipt_id: str | None = None
    content_type: str | None = None
    trend: str | None = None
    style: str | None = None
    caption: str | None = None
    media_path: str | None = None
    media_url: str | None = None
    linkage_context: dict[str, Any] | None = None
    raw_publish_result: dict[str, Any] | None = None
    error: str | None = None
    creation_id: str | None = None
    media_id: str | None = None
    permalink: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_placeholder_receipt(**kwargs: Any) -> PublishReceipt:
    created_at = kwargs.get("created_at") or datetime.utcnow().isoformat()
    return PublishReceipt(
        ok=bool(kwargs.get("ok", False)),
        publish_status=kwargs.get("publish_status") or "placeholder",
        created_at=created_at,
        receipt_id=kwargs.get("receipt_id") or f"receipt_{uuid.uuid4().hex}",
        content_type=kwargs.get("content_type"),
        trend=kwargs.get("trend"),
        style=kwargs.get("style"),
        caption=kwargs.get("caption"),
        media_path=kwargs.get("media_path"),
        media_url=kwargs.get("media_url"),
        linkage_context=kwargs.get("linkage_context"),
        raw_publish_result=kwargs.get("raw_publish_result"),
        error=kwargs.get("error") or "publish_placeholder_fallback",
        creation_id=kwargs.get("creation_id"),
        media_id=kwargs.get("media_id"),
        permalink=kwargs.get("permalink"),
    )


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

    def _normalize_payload(self, payload: PublishReceipt | dict[str, Any]) -> dict[str, Any]:
        if isinstance(payload, PublishReceipt):
            return payload.to_dict()
        return dict(payload or {})

    def save_receipt(self, receipt: PublishReceipt | dict[str, Any]) -> dict[str, Any]:
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

    def save_error(self, error: PublishReceipt | dict[str, Any]) -> dict[str, Any]:
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

    def _graph_request(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        timeout: int = 60,
    ) -> dict[str, Any]:
        token = self.config.ig_token
        if not token:
            return {"ok": False, "error": "IG_TOKEN ausente"}

        url = f"{self.config.graph_base_url.rstrip('/')}/{path.lstrip('/')}"
        payload = dict(data or {})
        query = dict(params or {})

        if method.upper() == "POST":
            payload["access_token"] = token
        else:
            query["access_token"] = token

        try:
            if method.upper() == "POST":
                response = requests.post(url, data=payload, timeout=timeout)
            else:
                response = requests.get(url, params=query, timeout=timeout)

            try:
                body = response.json()
            except Exception:
                body = {"raw": response.text[:4000]}

            if response.status_code >= 400:
                return {
                    "ok": False,
                    "status_code": response.status_code,
                    "error": body,
                    "url": url,
                }

            return {
                "ok": True,
                "status_code": response.status_code,
                "data": body,
                "url": url,
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc), "url": url}

    def _is_media_not_ready(self, result: dict[str, Any]) -> bool:
        error = (((result or {}).get("error") or {}).get("error") or {})
        code = error.get("code")
        subcode = error.get("error_subcode")
        message = str(error.get("message") or "").lower()
        user_message = str(error.get("error_user_msg") or "").lower()

        if code == 9007 and subcode == 2207027:
            return True

        combined = f"{message} {user_message}"
        return (
            "media id is not available" in combined
            or "mídia não está pronta" in combined
            or "media is not ready" in combined
        )

    def _publish_with_retry(
        self,
        *,
        ig_id: str,
        creation_id: str,
        attempts: int = 6,
        waits: tuple[int, ...] = (3, 5, 8, 12, 15, 20),
    ) -> dict[str, Any]:
        last_result: dict[str, Any] | None = None
        for idx in range(attempts):
            published = self._graph_request(
                "POST",
                f"{ig_id}/media_publish",
                data={"creation_id": creation_id},
            )
            last_result = published

            if published.get("ok"):
                return {
                    **published,
                    "retry_attempts": idx + 1,
                    "retry_waits": list(waits[:idx]),
                }

            if not self._is_media_not_ready(published):
                return {
                    **published,
                    "retry_attempts": idx + 1,
                    "retry_waits": list(waits[:idx]),
                }

            if idx < len(waits):
                time.sleep(waits[idx])

        return {
            **(last_result or {"ok": False, "error": "publish_retry_exhausted"}),
            "retry_attempts": attempts,
            "retry_waits": list(waits),
        }

    def _build_error_receipt(
        self,
        *,
        content_type: str,
        trend: str,
        style: str,
        caption: str,
        media_path: str | None,
        media_url: str | None,
        error: str,
        linkage_context: dict[str, Any] | None = None,
        raw_publish_result: dict[str, Any] | None = None,
        creation_id: str | None = None,
        media_id: str | None = None,
        permalink: str | None = None,
    ) -> dict[str, Any]:
        receipt = PublishReceipt(
            ok=False,
            publish_status="error",
            created_at=datetime.now().isoformat(),
            receipt_id=f"receipt_{uuid.uuid4().hex}",
            content_type=content_type,
            trend=trend,
            style=style,
            caption=caption,
            media_path=media_path,
            media_url=media_url,
            linkage_context=linkage_context,
            raw_publish_result=raw_publish_result,
            error=error,
            creation_id=creation_id,
            media_id=media_id,
            permalink=permalink,
        )
        return self.save_error(receipt)

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
        receipt = build_placeholder_receipt(
            created_at=datetime.now().isoformat(),
            receipt_id=f"receipt_{uuid.uuid4().hex}",
            content_type=content_type,
            trend=trend,
            style=style,
            caption=caption,
            media_path=media_path,
            media_url=self.build_media_url(media_path),
            linkage_context=linkage_context,
            raw_publish_result={
                "mode": "placeholder",
                "real_publish_enabled": self.config.enable_real_publish,
            },
            error="placeholder_mode",
        )
        saved = self.save_receipt(receipt)
        self.save_error(receipt)
        return saved

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
        ig_id = self.config.ig_id

        if not self.config.enable_real_publish:
            return self.publish_placeholder(
                trend=trend,
                style=style,
                content_type=content_type,
                caption=caption,
                media_path=media_path,
                linkage_context=linkage_context,
            )

        if not ig_id:
            return self._build_error_receipt(
                content_type=content_type,
                trend=trend,
                style=style,
                caption=caption,
                media_path=media_path,
                media_url=self.build_media_url(media_path),
                linkage_context=linkage_context,
                error="IG_ID ausente",
            )

        media_url = self.build_media_url(media_path)
        if not media_url:
            return self._build_error_receipt(
                content_type=content_type,
                trend=trend,
                style=style,
                caption=caption,
                media_path=media_path,
                media_url=None,
                linkage_context=linkage_context,
                error="media_url_indisponivel",
            )

        container = self._graph_request(
            "POST",
            f"{ig_id}/media",
            data={
                "image_url": media_url,
                "caption": caption[:2200],
            },
        )
        if not container.get("ok"):
            return self._build_error_receipt(
                content_type=content_type,
                trend=trend,
                style=style,
                caption=caption,
                media_path=media_path,
                media_url=media_url,
                linkage_context=linkage_context,
                error="container_fail",
                raw_publish_result={"container": container},
            )

        creation_id = ((container.get("data") or {}).get("id"))
        if not creation_id:
            return self._build_error_receipt(
                content_type=content_type,
                trend=trend,
                style=style,
                caption=caption,
                media_path=media_path,
                media_url=media_url,
                linkage_context=linkage_context,
                error="creation_id_ausente",
                raw_publish_result={"container": container},
            )

        published = self._publish_with_retry(
            ig_id=str(ig_id),
            creation_id=str(creation_id),
        )
        if not published.get("ok"):
            return self._build_error_receipt(
                content_type=content_type,
                trend=trend,
                style=style,
                caption=caption,
                media_path=media_path,
                media_url=media_url,
                linkage_context=linkage_context,
                error="publish_fail",
                raw_publish_result={"container": container, "published": published},
                creation_id=creation_id,
            )

        media_id = ((published.get("data") or {}).get("id"))
        permalink = None
        info = None

        if media_id:
            info = self._graph_request(
                "GET",
                str(media_id),
                params={"fields": "id,permalink"},
            )
            if info.get("ok"):
                permalink = ((info.get("data") or {}).get("permalink"))

        receipt = PublishReceipt(
            ok=True,
            publish_status="published",
            created_at=datetime.now().isoformat(),
            receipt_id=f"receipt_{uuid.uuid4().hex}",
            content_type=content_type,
            trend=trend,
            style=style,
            caption=caption,
            media_path=media_path,
            media_url=media_url,
            linkage_context=linkage_context,
            raw_publish_result={
                "container": container,
                "published": published,
                "info": info,
            },
            error=None,
            creation_id=creation_id,
            media_id=media_id,
            permalink=permalink,
        )
        return self.save_receipt(receipt)
