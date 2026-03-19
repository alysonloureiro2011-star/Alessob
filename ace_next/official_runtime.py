from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import AceNextConfig
from .legacy_bridge import get_legacy_memory_summary, run_legacy_pipeline
from .publish import PublishService


@dataclass
class OfficialRuntimeState:
    runtime_mode: str = "ACE_NEXT_OFFICIAL_CORE"
    official_content_handler: str = "ace_next.official_runtime.OfficialRuntime.run"
    official_publish_handler: str = "legacy_pipeline_then_receipt_persistence"
    official_queue_handler: str = "manual"
    last_runtime_action: str | None = None
    last_runtime_error: str | None = None
    last_runtime_action_at: str | None = None
    last_pipeline_source: str | None = None


class OfficialRuntime:
    def __init__(self, config: AceNextConfig) -> None:
        self.config = config
        self.publish = PublishService(config)
        self.state = OfficialRuntimeState()

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
            return {"ok": False, "error": str(exc)}

    def _persist_receipt_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.publish.receipt_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    def run_placeholder(self, trend: str | None = None) -> dict[str, Any]:
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

        self._touch("run_placeholder", None, "ace_next_placeholder")
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

    def run_legacy(self, trend: str | None = None) -> dict[str, Any]:
        trend = (trend or "disciplina com inteligência").strip()
        try:
            result = run_legacy_pipeline(trend=trend)
            published = (result or {}).get("published") or {}
            receipt = published.get("publish_receipt") or {}
            publish_result = published.get("publish_result") or {}
            plan = (result or {}).get("plan") or {}
            content = (result or {}).get("content") or {}
            media = (result or {}).get("media") or {}

            payload = {
                "ok": bool(receipt.get("ok", False)),
                "publish_status": receipt.get("publish_status") or published.get("status") or "generated",
                "created_at": receipt.get("published_at") or published.get("created_at") or datetime.now().isoformat(),
                "content_type": plan.get("content_type") or "unknown",
                "trend": result.get("trend"),
                "style": plan.get("style"),
                "caption": content.get("caption"),
                "media_path": receipt.get("media_path") or media.get("media_path"),
                "media_url": receipt.get("media_url"),
                "raw_publish_result": publish_result if isinstance(publish_result, dict) else None,
                "error": publish_result.get("error") if isinstance(publish_result, dict) else receipt.get("detail"),
            }
            self._persist_receipt_payload(payload)
            if not payload["ok"]:
                self.publish.save_error(payload)

            self._touch("run_legacy", None, "legacy_pipeline")
            return {
                "ok": True,
                "mode": "legacy_pipeline",
                "result": result,
                "memory": self.get_memory_summary(),
                "last_publish_receipt": payload,
            }
        except Exception as exc:
            self._touch("run_legacy", str(exc), "legacy_pipeline")
            return {
                "ok": False,
                "mode": "legacy_pipeline",
                "error": str(exc),
                "fallback": self.run_placeholder(trend=trend),
            }

    def run(self, trend: str | None = None, force_placeholder: bool = False) -> dict[str, Any]:
        if force_placeholder:
            return self.run_placeholder(trend=trend)
        return self.run_legacy(trend=trend)
