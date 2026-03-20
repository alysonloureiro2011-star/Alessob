from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .auth_store import load_instagram_auth, sync_instagram_token_sources
from .config import AceNextConfig
from .legacy_bridge import get_legacy_memory_summary, run_legacy_pipeline
from .official_instagram_publish import OfficialInstagramPublishService
from .publish import PublishReceipt, PublishService, build_placeholder_receipt


@dataclass
class OfficialRuntimeState:
    runtime_mode: str = "ACE_NEXT_OFFICIAL_CORE"
    official_content_handler: str = "ace_next.official_runtime.OfficialRuntime.run"
    official_publish_handler: str = (
        "ace_next.official_instagram_publish.OfficialInstagramPublishService"
    )
    official_queue_handler: str = "manual"
    last_runtime_action: str | None = None
    last_runtime_error: str | None = None
    last_runtime_action_at: str | None = None
    last_pipeline_source: str | None = None
    instagram_auth_loaded_at: str | None = None


class OfficialRuntime:
    def __init__(
        self,
        config: AceNextConfig,
        publish_service: PublishService | None = None,
    ) -> None:
        self.config = config
        self.publish = publish_service or PublishService(config)
        self.instagram = OfficialInstagramPublishService(config)
        self.state = OfficialRuntimeState()
        self._load_instagram_auth_on_boot()

    def _load_instagram_auth_on_boot(self) -> dict[str, Any]:
        loaded = load_instagram_auth(self.config)
        synced = sync_instagram_token_sources(
            self.config,
            runtime_token=loaded.get("token"),
            runtime_user_id=(loaded.get("user_id") or loaded.get("ig_id")),
        )
        self.state.instagram_auth_loaded_at = datetime.now().isoformat()
        return {"loaded": loaded, "synced": synced}

    def sync_instagram_auth(self) -> dict[str, Any]:
        synced = sync_instagram_token_sources(
            self.config,
            runtime_token=self.config.ig_token,
            runtime_user_id=self.config.ig_id,
        )
        self.state.instagram_auth_loaded_at = datetime.now().isoformat()
        return synced

    def instagram_readiness(self) -> dict[str, Any]:
        return self.instagram.readiness()

    def snapshot(self) -> dict[str, Any]:
        last_publish = self.publish.last_publish()
        data = asdict(self.state)
        data["render_url"] = self.config.render_url
        data["auth_path"] = str(self.config.auth_path)
        data["real_publish_enabled"] = self.config.enable_real_publish
        data["token_present"] = bool(self.config.ig_token)
        data["ig_id_present"] = bool(self.config.ig_id)
        data["instagram_readiness"] = self.instagram_readiness()
        data["last_receipt"] = last_publish.get("last_publish_receipt")
        data["last_error"] = last_publish.get("last_publish_error")
        data["last_episode"] = last_publish.get("last_episode")
        return data

    def _touch(
        self,
        action: str,
        error: str | None = None,
        source: str | None = None,
    ) -> None:
        self.state.last_runtime_action = action
        self.state.last_runtime_error = error
        self.state.last_runtime_action_at = datetime.now().isoformat()
        if source:
            self.state.last_pipeline_source = source

    def get_memory_summary(self) -> dict[str, Any]:
        try:
            return get_legacy_memory_summary()
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def _extract_media_paths(self, media: dict[str, Any]) -> list[str]:
        if not isinstance(media, dict):
            return []

        media_paths = media.get("media_paths")
        if isinstance(media_paths, list):
            return [str(path) for path in media_paths if path]

        media_path = media.get("media_path")
        if media_path:
            return [str(media_path)]

        return []

    def _normalize_publish_contract(
        self,
        *,
        content_type: str | None,
        media_paths: list[str],
    ) -> dict[str, Any]:
        requested_content_type = str(content_type or "reel").strip().lower() or "reel"
        effective_content_type = requested_content_type
        normalization_applied = False
        normalization_reason = None
        normalized_media_paths = [str(path) for path in (media_paths or []) if path]
        media_path = normalized_media_paths[0] if normalized_media_paths else None

        if requested_content_type == "carrossel":
            if len(normalized_media_paths) == 1:
                effective_content_type = "imagem"
                normalization_applied = True
                normalization_reason = "single_media_carousel_downgrade"
            elif len(normalized_media_paths) == 0:
                normalization_reason = "carousel_without_media"

        return {
            "requested_content_type": requested_content_type,
            "effective_content_type": effective_content_type,
            "normalization_applied": normalization_applied,
            "normalization_reason": normalization_reason,
            "media_paths": normalized_media_paths,
            "media_path": media_path,
        }

    def _build_receipt(
        self,
        *,
        ok: bool,
        publish_status: str,
        created_at: str,
        content_type: str | None,
        trend: str | None,
        style: str | None,
        caption: str | None,
        media_path: str | None,
        media_url: str | None,
        raw_publish_result: dict[str, Any] | None,
        error: str | None,
        creation_id: str | None,
        media_id: str | None,
        permalink: str | None,
    ) -> PublishReceipt:
        return PublishReceipt(
            ok=ok,
            publish_status=publish_status,
            created_at=created_at,
            content_type=content_type,
            trend=trend,
            style=style,
            caption=caption,
            media_path=media_path,
            media_url=media_url,
            raw_publish_result=raw_publish_result,
            error=error,
            creation_id=creation_id,
            media_id=media_id,
            permalink=permalink,
        )

    def run_placeholder(self, trend: str | None = None) -> dict[str, Any]:
        normalized_trend = (trend or "disciplina com inteligência").strip()
        style = "premium"
        content_type = "reel"
        caption = f"ACE Ω NEXT | {normalized_trend}"

        media_dir = Path(self.config.media_dir)
        media_dir.mkdir(parents=True, exist_ok=True)
        media_path = str(media_dir / "ace_next_placeholder.txt")
        Path(media_path).write_text(caption, encoding="utf-8")

        receipt = self.publish.publish_placeholder(
            trend=normalized_trend,
            style=style,
            content_type=content_type,
            caption=caption,
            media_path=media_path,
        )

        self._touch("run_placeholder", None, "ace_next_placeholder")

        return {
            "ok": False,
            "mode": "placeholder",
            "trend": normalized_trend,
            "style": style,
            "content_type": content_type,
            "caption": caption,
            "media_path": media_path,
            "publish_receipt": receipt,
            "instagram_readiness": self.instagram_readiness(),
        }

    def run_legacy(self, trend: str | None = None) -> dict[str, Any]:
        created_at = datetime.utcnow().isoformat()

        try:
            pipeline = run_legacy_pipeline(trend=trend)
        except Exception as exc:
            self._touch("run_legacy_boot_fail", str(exc), "legacy_pipeline")
            fallback = build_placeholder_receipt(
                created_at=created_at,
                content_type="unknown",
                trend=trend,
                style=None,
                caption=None,
                media_path=None,
                media_url=None,
                raw_publish_result=None,
                error=str(exc),
            )
            self.publish.save_error(fallback)
            return {
                "ok": False,
                "mode": "legacy_pipeline",
                "error": str(exc),
                "instagram_readiness": self.instagram_readiness(),
                "fallback": fallback.to_dict(),
            }

        plan = pipeline.get("plan") or {}
        content = pipeline.get("content") or {}
        media = pipeline.get("media") or {}

        content_type = (
            plan.get("content_type")
            or content.get("content_type")
            or media.get("content_type")
            or "reel"
        )
        style = plan.get("style") or content.get("style")
        normalized_trend = trend or pipeline.get("trend")
        caption = (
            content.get("caption")
            or content.get("text")
            or content.get("body")
            or ""
        )

        contract = self._normalize_publish_contract(
            content_type=content_type,
            media_paths=self._extract_media_paths(media),
        )
        requested_content_type = contract["requested_content_type"]
        effective_content_type = contract["effective_content_type"]
        media_paths = contract["media_paths"]
        media_path = contract["media_path"]

        publish_result: dict[str, Any] | None = None

        try:
            if effective_content_type == "carrossel":
                publish_result = self.instagram.publish_carousel(
                    media_paths=media_paths,
                    caption=caption,
                )
            else:
                publish_result = self.instagram.publish_single(
                    media_path=media_path,
                    caption=caption,
                    content_type=effective_content_type,
                )

            publish_result = {
                **contract,
                **dict(publish_result or {}),
            }

            receipt = self._build_receipt(
                ok=bool(publish_result.get("ok")),
                publish_status="published" if publish_result.get("ok") else "failed",
                created_at=created_at,
                content_type=effective_content_type,
                trend=normalized_trend,
                style=style,
                caption=caption,
                media_path=media_path,
                media_url=publish_result.get("media_url"),
                raw_publish_result=publish_result,
                error=publish_result.get("error"),
                creation_id=publish_result.get("creation_id"),
                media_id=publish_result.get("media_id"),
                permalink=publish_result.get("permalink"),
            )

            pipeline["publish_receipt"] = (
                self.publish.save_receipt(receipt)
                if receipt.ok
                else self.publish.save_error(receipt)
            )
            pipeline["instagram_readiness"] = self.instagram_readiness()

            self._touch(
                "run_legacy",
                None if receipt.ok else receipt.error,
                "legacy_pipeline_plus_official_publish",
            )

            return {
                "ok": bool(receipt.ok),
                "mode": "legacy_pipeline",
                "result": pipeline,
                "memory": self.get_memory_summary(),
                "last_publish_receipt": pipeline["publish_receipt"],
                "instagram_readiness": self.instagram_readiness(),
                "requested_content_type": requested_content_type,
                "effective_content_type": effective_content_type,
                "normalization_applied": contract["normalization_applied"],
                "normalization_reason": contract["normalization_reason"],
            }

        except Exception as exc:
            publish_result = {
                **contract,
                **dict(publish_result or {}),
            }

            placeholder = build_placeholder_receipt(
                created_at=created_at,
                content_type=effective_content_type,
                trend=normalized_trend,
                style=style,
                caption=caption,
                media_path=media_path,
                media_url=self.publish.build_media_url(media_path),
                raw_publish_result=publish_result,
                error=str(exc),
            )

            saved_error = self.publish.save_error(placeholder)
            pipeline["publish_receipt"] = saved_error
            pipeline["instagram_readiness"] = self.instagram_readiness()

            self._touch(
                "run_legacy_publish_fail",
                str(exc),
                "legacy_pipeline_plus_official_publish",
            )

            return {
                "ok": False,
                "mode": "legacy_pipeline",
                "result": pipeline,
                "error": str(exc),
                "memory": self.get_memory_summary(),
                "last_publish_receipt": saved_error,
                "instagram_readiness": self.instagram_readiness(),
                "fallback": placeholder.to_dict(),
                "requested_content_type": requested_content_type,
                "effective_content_type": effective_content_type,
                "normalization_applied": contract["normalization_applied"],
                "normalization_reason": contract["normalization_reason"],
            }

    def run(
        self,
        trend: str | None = None,
        force_placeholder: bool = False,
    ) -> dict[str, Any]:
        if force_placeholder:
            return self.run_placeholder(trend=trend)
        return self.run_legacy(trend=trend)
