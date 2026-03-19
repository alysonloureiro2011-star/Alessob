from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import AceNextConfig
from .publish import PublishService


@dataclass
class RuntimeState:
    runtime_mode: str = "ACE_NEXT_CLEAN"
    official_content_handler: str = "ace_next.runtime.generate_once"
    official_publish_handler: str = "ace_next.publish.PublishService.publish_placeholder"
    official_queue_handler: str = "manual"
    last_runtime_action: str | None = None
    last_runtime_error: str | None = None
    last_runtime_action_at: str | None = None


class AceNextRuntime:
    def __init__(self, config: AceNextConfig) -> None:
        self.config = config
        self.publish = PublishService(config)
        self.state = RuntimeState()

    def snapshot(self) -> dict[str, Any]:
        data = asdict(self.state)
        data["render_url"] = self.config.render_url
        data["real_publish_enabled"] = self.config.enable_real_publish
        data["token_present"] = bool(self.config.ig_token)
        data["ig_id_present"] = bool(self.config.ig_id)
        return data

    def _touch(self, action: str, error: str | None = None) -> None:
        self.state.last_runtime_action = action
        self.state.last_runtime_error = error
        self.state.last_runtime_action_at = datetime.now().isoformat()

    def generate_once(self, trend: str | None = None) -> dict[str, Any]:
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

        self._touch("generate_once", None)
        return {
            "ok": True,
            "trend": trend,
            "style": style,
            "content_type": content_type,
            "caption": caption,
            "media_path": media_path,
            "publish_receipt": receipt,
        }
