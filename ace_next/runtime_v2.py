from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import AceNextConfig
from .legacy_bridge import get_legacy_memory_summary, run_legacy_pipeline
from .publish import PublishService


@dataclass
class RuntimeStateV2:
    runtime_mode: str = "ACE_NEXT_CLEAN_V2"
    official_content_handler: str = "ace_next.runtime_v2.AceNextRuntimeV2.generate_or_bridge"
    official_publish_handler: str = "legacy_pipeline_then_ace_next_receipt"
    official_queue_handler: str = "manual"
    last_runtime_action: str | None = None
    last_runtime_error: str | None = None
    last_runtime_action_at: str | None = None
    last_pipeline_source: str | None = None


class AceNextRuntimeV2:
    def __init__(self, config: AceNextConfig) -> None:
        self.config = config
        self.publish = PublishService(config)
        self.state = RuntimeStateV2()

    def snapshot(self) -> dict[str, Any]:
        data = asdict(self.state)
        data["render_url"] = self.config.render_url
        data["real_publish_enabled"] = self.config.enable_real_publish
        data["token_present"] = bool(self.config.ig_token)
        data["ig_id_present"] = bool(self.config.ig_id)
        return data

    def _touch(self, action: str, error: str | None = None, source: str | None = None) -> None:
        self.state.last_runtime_action = action
        self.state.last_runtime_error = error
        self.state.last_runtime_action_at = datetime.now().isoformat()
        if source:
            self.state.last_pipeline_source = source

    def get_memory_summary(self) -> dict[str, Any]:
        try:
            return get_legacy_memory_summary()
        except Exception as exc:
            return {
                "ok": False,
                "error": str(exc),
            }

    def generate_placeholder(self, trend: str | None = None) -> dict[str, Any]:
        trend = (trend or "disciplina com inteligência").strip()
        style = "premium"
        content_type = "reel"
        caption = f"ACE Ω NEXT | {trend}"

        media_dir = Path(self.config.media_dir)
        media_dir.mkdir(parents=True, exist_ok=True)
        media_path = str(media_dir / "ace_next_placeholder.txt")
        Path(media_path).write_text(caption, encoding="utf-8")

        receipt = self.publish.publish_placeholder(
            trend=trend,
            style=style,
            content_type=content_type,
            caption=caption,
            media_path=media_path,
        )

        self._touch("generate_placeholder", None, "ace_next_placeholder")
        return {
            "ok": True,
            "mode": "placeholder",
            "trend": trend,
            "style": style,
            "content_type": content_type,
            "caption": caption,
            "media_path": media_path,
            "publish_receipt": receipt,
        }

    def generate_via_legacy_pipeline(self, trend: str | None = None) -> dict[str, Any]:
        trend = (trend or "disciplina com inteligência").strip()
        try:
            result = run_legacy_pipeline(trend=trend)
            published = (result or {}).get("published") or {}
            receipt = published.get("publish_receipt")
            publish_result = published.get("publish_result")
            if isinstance(receipt, dict):
                payload = {
                    **receipt,
                    "trend": result.get("trend"),
                    "style": ((result.get("plan") or {}).get("style")),
                    "content_type": ((result.get("plan") or {}).get("content_type")),
                    "raw_publish_result": publish_result if isinstance(publish_result, dict) else None,
                }
                self.publish.save_receipt(type("ReceiptLike", (), {"__dict__": payload})())
            elif isinstance(publish_result, dict):
                self.publish.save_error(publish_result)

            self._touch("generate_via_legacy_pipeline", None, "legacy_pipeline")
            return {
                "ok": True,
                "mode": "legacy_pipeline",
                "result": result,
                "memory": self.get_memory_summary(),
            }
        except Exception as exc:
            self._touch("generate_via_legacy_pipeline", str(exc), "legacy_pipeline")
            return {
                "ok": False,
                "mode": "legacy_pipeline",
                "error": str(exc),
                "fallback": self.generate_placeholder(trend=trend),
            }

    def generate_or_bridge(self, trend: str | None = None, force_placeholder: bool = False) -> dict[str, Any]:
        if force_placeholder:
            return self.generate_placeholder(trend=trend)
        return self.generate_via_legacy_pipeline(trend=trend)
