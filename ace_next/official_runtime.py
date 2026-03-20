from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from .auth_store import sync_instagram_token_sources
from .config import AceNextConfig
from .publish import PublishService

try:
    from PIL import Image, ImageDraw
except Exception:
    Image = None
    ImageDraw = None


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
            "enable_real_publish": self.config.enable_real_publish,
        }

    def _build_test_image(self, trend: str) -> str:
        self.config.media_dir.mkdir(parents=True, exist_ok=True)
        out = self.config.media_dir / f"ace_next_{uuid.uuid4().hex}.png"

        if Image is None or ImageDraw is None:
            out.write_bytes(
                bytes.fromhex(
                    "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4890000000D49444154789C63F8FFFFFF7F0009FB03FD2A86E38A0000000049454E44AE426082"
                )
            )
            return str(out)

        img = Image.new("RGB", (1080, 1350), (250, 248, 244))
        draw = ImageDraw.Draw(img)

        title = "ACE Ω NEXT"
        body = (trend or "teste real").strip()[:80]

        draw.rectangle((0, 0, 1080, 180), fill=(20, 20, 20))
        draw.text((60, 70), title, fill=(255, 255, 255))
        draw.text((60, 320), body, fill=(20, 20, 20))
        draw.text((60, 1180), "@ace_next", fill=(90, 90, 90))

        img.save(out)
        return str(out)

    def run(
        self,
        *,
        trend: str,
        force_placeholder: bool = False,
    ) -> dict:
        trend = (trend or "teste real").strip()
        style = "official_next"
        content_type = "image"
        caption = f"ACE Ω NEXT | {trend}"

        media_path = None
        if not force_placeholder:
            media_path = self._build_test_image(trend)

        if force_placeholder:
            publish_result = self.publish.publish_placeholder(
                trend=trend,
                style=style,
                content_type=content_type,
                caption=caption,
                media_path=media_path,
            )
            mode = "placeholder"
        else:
            publish_result = self.publish.publish_real(
                trend=trend,
                style=style,
                content_type=content_type,
                caption=caption,
                media_path=media_path,
            )
            mode = "real" if publish_result.get("ok") else "error"

        return {
            "ok": True,
            "mode": mode,
            "force_placeholder": force_placeholder,
            "trend": trend,
            "runtime": self.snapshot(),
            "publish_result": publish_result,
            "last_publish": self.publish.last_publish(),
        }
