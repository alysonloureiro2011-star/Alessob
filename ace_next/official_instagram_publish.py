from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

from .config import AceNextConfig


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


class OfficialInstagramPublishService:
    def __init__(self, config: AceNextConfig) -> None:
        self.config = config

    def token(self) -> str | None:
        return self.config.ig_token

    def ig_id(self) -> str | None:
        return self.config.ig_id

    def readiness(self) -> dict[str, Any]:
        return {
            "instagram_connected": bool(self.token() and self.ig_id()),
            "token_present": bool(self.token()),
            "ig_id_present": bool(self.ig_id()),
            "ig_id": self.ig_id(),
            "real_publish_enabled": bool(self.config.enable_real_publish),
            "public_media_base_url": self.config.public_media_base_url,
            "graph_base_url": self.config.graph_base_url,
        }

    def media_public_url_from_path(self, media_path: str | None) -> str | None:
        if not media_path:
            return None
        filename = Path(media_path).name
        if not filename:
            return None
        return f"{self.config.public_media_base_url.rstrip('/')}/media/{filename}"

    def media_kind_from_path(self, media_path: str | None, content_type: str = "reel") -> str:
        ext = (Path(media_path).suffix or "").lower() if media_path else ""
        ctype = (content_type or "").lower()
        if ctype == "reel":
            return "reel"
        if ext in (".mp4", ".mov", ".m4v"):
            return "video"
        return "image"

    def instagram_request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        json_payload: dict[str, Any] | None = None,
        timeout: int = 60,
    ) -> dict[str, Any]:
        token = self.token()
        if not token:
            return {"ok": False, "error": "IG_TOKEN ausente"}

        url = f"{self.config.graph_base_url.rstrip('/')}/{path.lstrip('/')}"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(
                    url,
                    params=params,
                    data=data,
                    json=json_payload,
                    headers=headers,
                    timeout=timeout,
                )
            else:
                return {"ok": False, "error": f"metodo_unsupported:{method}"}

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
            return {
                "ok": False,
                "error": str(exc),
                "url": url,
            }

    def ig_post(self, path: str, data: dict[str, Any], timeout: int = 90) -> dict[str, Any]:
        payload = dict(data or {})
        payload["access_token"] = self.token()
        return self.instagram_request("POST", path, data=payload, timeout=timeout)

    def fetch_permalink(self, media_id: str | None) -> dict[str, Any]:
        if not media_id:
            return {"ok": False, "error": "media_id ausente"}
        return self.instagram_request(
            "GET",
            f"{media_id}",
            params={"fields": "permalink"},
            timeout=60,
        )

    def create_single_media_container(
        self,
        media_url: str,
        caption: str = "",
        media_kind: str = "image",
    ) -> dict[str, Any]:
        ig_id = self.ig_id()
        if not ig_id:
            return {"ok": False, "error": "IG_ID ausente"}
        if not media_url:
            return {"ok": False, "error": "media_url ausente"}

        path = f"{ig_id}/media"

        if media_kind == "reel":
            data = {
                "media_type": "REELS",
                "video_url": media_url,
                "caption": caption[:2200],
            }
        elif media_kind == "video":
            data = {
                "media_type": "VIDEO",
                "video_url": media_url,
                "caption": caption[:2200],
            }
        else:
            data = {
                "image_url": media_url,
                "caption": caption[:2200],
            }

        return self.ig_post(path, data, timeout=90)

    def create_carousel_child_container(self, media_url: str, media_kind: str = "image") -> dict[str, Any]:
        ig_id = self.ig_id()
        if not ig_id:
            return {"ok": False, "error": "IG_ID ausente"}
        if not media_url:
            return {"ok": False, "error": "media_url ausente"}

        path = f"{ig_id}/media"

        if media_kind == "video":
            data = {
                "media_type": "VIDEO",
                "video_url": media_url,
                "is_carousel_item": "true",
            }
        else:
            data = {
                "image_url": media_url,
                "is_carousel_item": "true",
            }

        return self.ig_post(path, data, timeout=90)

    def create_carousel_container(self, children_ids: list[str], caption: str = "") -> dict[str, Any]:
        ig_id = self.ig_id()
        if not ig_id:
            return {"ok": False, "error": "IG_ID ausente"}
        if not children_ids:
            return {"ok": False, "error": "children_ids ausente"}

        path = f"{ig_id}/media"
        data = {
            "media_type": "CAROUSEL",
            "children": ",".join(children_ids),
            "caption": caption[:2200],
        }
        return self.ig_post(path, data, timeout=90)

    def publish_media_container(self, creation_id: str) -> dict[str, Any]:
        ig_id = self.ig_id()
        if not ig_id:
            return {"ok": False, "error": "IG_ID ausente"}
        if not creation_id:
            return {"ok": False, "error": "creation_id ausente"}
        return self.ig_post(f"{ig_id}/media_publish", {"creation_id": creation_id}, timeout=90)

    def publish_single(self, caption: str, media_path: str | None, content_type: str = "reel") -> dict[str, Any]:
        if not self.config.enable_real_publish:
            return {"ok": False, "reason": "real_publish_disabled"}
        if not self.token() or not self.ig_id():
            return {"ok": False, "reason": "ig_id_ou_token_ausente"}

        media_url = self.media_public_url_from_path(media_path)
        if not media_url:
            return {"ok": False, "reason": "media_url_indisponivel"}

        media_kind = self.media_kind_from_path(media_path, content_type=content_type)
        if content_type == "reel":
            media_kind = "reel"

        container = self.create_single_media_container(
            media_url=media_url,
            caption=caption,
            media_kind=media_kind,
        )
        if not container.get("ok"):
            return {"ok": False, "reason": "container_fail", "detail": container}

        creation_id = _safe_dict(container.get("data")).get("id")
        if not creation_id:
            return {"ok": False, "reason": "creation_id_ausente", "detail": container}

        published = self.publish_media_container(creation_id)
        if not published.get("ok"):
            return {"ok": False, "reason": "publish_fail", "detail": published}

        published_data = _safe_dict(published.get("data"))
        media_id = published_data.get("id")

        permalink_lookup = self.fetch_permalink(media_id)
        permalink = None
        if permalink_lookup.get("ok"):
            permalink = _safe_dict(permalink_lookup.get("data")).get("permalink")

        return {
            "ok": True,
            "media_url": media_url,
            "container": _safe_dict(container.get("data")),
            "published": published_data,
            "media_id": media_id,
            "permalink": permalink,
            "permalink_lookup": permalink_lookup,
        }

    def publish_carousel(self, caption: str, media_paths: list[str]) -> dict[str, Any]:
        if not self.config.enable_real_publish:
            return {"ok": False, "reason": "real_publish_disabled"}
        if not self.token() or not self.ig_id():
            return {"ok": False, "reason": "ig_id_ou_token_ausente"}
        if not media_paths or len(media_paths) < 2:
            return {"ok": False, "reason": "carrossel_precisa_de_2_ou_mais_midias"}

        child_ids: list[str] = []
        child_debug: list[dict[str, Any]] = []

        for media_path in media_paths:
            media_url = self.media_public_url_from_path(media_path)
            if not media_url:
                return {"ok": False, "reason": "media_url_indisponivel", "media_path": media_path}

            media_kind = self.media_kind_from_path(media_path, content_type="carousel")
            if media_kind == "reel":
                media_kind = "video"

            child = self.create_carousel_child_container(media_url=media_url, media_kind=media_kind)
            child_debug.append(child)

            if not child.get("ok"):
                return {
                    "ok": False,
                    "reason": "child_container_fail",
                    "detail": child,
                    "children_debug": child_debug,
                }

            child_id = _safe_dict(child.get("data")).get("id")
            if not child_id:
                return {
                    "ok": False,
                    "reason": "child_id_ausente",
                    "detail": child,
                    "children_debug": child_debug,
                }

            child_ids.append(child_id)

        parent = self.create_carousel_container(children_ids=child_ids, caption=caption)
        if not parent.get("ok"):
            return {
                "ok": False,
                "reason": "carousel_parent_fail",
                "detail": parent,
                "children_debug": child_debug,
            }

        creation_id = _safe_dict(parent.get("data")).get("id")
        if not creation_id:
            return {"ok": False, "reason": "carousel_creation_id_ausente", "detail": parent}

        published = self.publish_media_container(creation_id)
        if not published.get("ok"):
            return {"ok": False, "reason": "carousel_publish_fail", "detail": published}

        published_data = _safe_dict(published.get("data"))
        media_id = published_data.get("id")

        permalink_lookup = self.fetch_permalink(media_id)
        permalink = None
        if permalink_lookup.get("ok"):
            permalink = _safe_dict(permalink_lookup.get("data")).get("permalink")

        return {
            "ok": True,
            "children_ids": child_ids,
            "parent": _safe_dict(parent.get("data")),
            "published": published_data,
            "media_id": media_id,
            "permalink": permalink,
            "permalink_lookup": permalink_lookup,
            "children_debug": child_debug,
        }
