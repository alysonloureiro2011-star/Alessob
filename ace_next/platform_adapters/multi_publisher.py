from __future__ import annotations
from typing import Any, Dict
from .youtube import YouTubeAdapter
from .tiktok import TikTokAdapter
from .threads import ThreadsAdapter

class MultiPlatformPublisher:
    """
    Agregador que publica simultaneamente em YouTube, TikTok e Threads.
    Útil para futuros fluxos multiplataforma.
    """

    def __init__(self, config: Any | None = None) -> None:
        self.youtube = YouTubeAdapter(config)
        self.tiktok = TikTokAdapter(config)
        self.threads = ThreadsAdapter(config)

    def publish_all(
        self,
        *,
        caption: str,
        media_path: str | None,
        metadata: Dict[str, Any] | None,
        dry_run: bool = True,
        linkage_context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        return {
            "youtube": self.youtube.publish(
                caption=caption,
                media_path=media_path,
                metadata=metadata,
                dry_run=dry_run,
                linkage_context=linkage_context,
            ),
            "tiktok": self.tiktok.publish(
                caption=caption,
                media_path=media_path,
                metadata=metadata,
                dry_run=dry_run,
                linkage_context=linkage_context,
            ),
                "threads": self.threads.publish(
                caption=caption,
                media_path=media_path,
                metadata=metadata,
                dry_run=dry_run,
                linkage_context=linkage_context,
            ),
        }
