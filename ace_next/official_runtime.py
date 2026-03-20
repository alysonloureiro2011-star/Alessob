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

    def _boot_sync(self):
        sync_instagram_token_sources(self.config)

    def sync_instagram_auth(self):
        return sync_instagram_token_sources(self.config)

    def snapshot(self):
        return {
            "timestamp": datetime.now().isoformat(),
            "token_present": bool(self.config.ig_token),
            "ig_id_present": bool(self.config.ig_id),
            "render_url": self.config.render_url,
        }
