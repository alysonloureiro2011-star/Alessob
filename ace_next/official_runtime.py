from __future__ import annotations

from datetime import datetime

from .auth_store import sync_instagram_token_sources
from .config import AceNextConfig
from .publish import PublishService


class OfficialRuntime:
    def __init__(self, config: AceNextConfig):
        self.config = config
        self.publish = PublishService(config)
        self._boot_sync()

    def _boot_sync(self) -> None:
        sync_instagram_token_sources(self.config)

    def sync_instagram_auth(self) -> dict:
        return sync_instagram_token_sources(self.config)

    def snapshot(self) -> dict:
        sync = self.sync_instagram_auth()
        return {
            "timestamp": datetime.now().isoformat(),
            "token_present": bool(self.config.ig_token),
            "ig_id_present": bool(self.config.ig_id),
            "render_url": self.config.render_url,
            "token_source": sync.get("token_source"),
            "user_id_source": sync.get("user_id_source"),
            "auth_path": sync.get("auth_path"),
        }

    def run(
        self,
        *,
        trend: str,
        force_placeholder: bool = False,
    ) -> dict:
        trend = (trend or "teste real").strip()
        style = "official_next"
        content_type = "reel"
        caption = f"ACE Ω NEXT | {trend}"

        receipt = self.publish.publish_placeholder(
            trend=trend,
            style=style,
            content_type=content_type,
            caption=caption,
            media_path=None,
        )

        return {
            "ok": True,
            "mode": "placeholder",
            "force_placeholder": force_placeholder,
            "trend": trend,
            "runtime": self.snapshot(),
            "publish_result": receipt,
            "last_publish": self.publish.last_publish(),
        }
