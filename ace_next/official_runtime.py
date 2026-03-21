from __future__ import annotations

import os
import textwrap
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from .auth_store import load_instagram_auth, sync_instagram_token_sources
from .config import AceNextConfig
from .creative_planner import build_creative_plan
from .publish import PublishService
from .render_env_sync import persist_instagram_token_to_render
from .token_upgrade import refresh_instagram_long_lived_token

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:
    Image = None
    ImageDraw = None
    ImageFont = None


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


class OfficialRuntime:
    def __init__(self, config: AceNextConfig):
        self.config = config
        self.publish = PublishService(config)
        self._boot_sync()

    def _refresh_threshold_days(self) -> int:
        try:
            return int(os.environ.get("ACE_TOKEN_REFRESH_THRESHOLD_DAYS", "15"))
        except Exception:
            return 15

    def _min_refresh_age_hours(self) -> int:
        try:
            return int(os.environ.get("ACE_TOKEN_MIN_REFRESH_AGE_HOURS", "24"))
        except Exception:
            return 24

    def _assumed_ttl_days(self) -> int:
        try:
            return int(os.environ.get("ACE_TOKEN_ASSUMED_TTL_DAYS", "60"))
        except Exception:
            return 60

    def _auth_state(self) -> dict[str, Any]:
        stored = load_instagram_auth(self.config)
        meta = stored.get("meta") if isinstance(stored.get("meta"), dict) else {}

        saved_at = _parse_dt(stored.get("saved_at"))
        expires_at = _parse_dt(meta.get("expires_at"))

        if not expires_at and saved_at:
            expires_at = saved_at + timedelta(days=self._assumed_ttl_days())

        now = datetime.now(timezone.utc)
        remaining_days = None
        if expires_at:
            remaining_days = (expires_at - now).total_seconds() / 86400

        return {
            "saved_at": saved_at.isoformat() if saved_at else None,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "remaining_days": remaining_days,
            "refreshed_at": meta.get("refreshed_at"),
            "source": meta.get("source"),
        }

    def _token_needs_refresh(self, force: bool = False) -> tuple[bool, str]:
        if force:
            return True, "forced"

        if not self.config.ig_token or not self.config.ig_id:
            return False, "missing_token_or_ig_id"

        state = self._auth_state()
        expires_at = _parse_dt(state.get("expires_at"))
        saved_at = _parse_dt(state.get("saved_at"))
        now = datetime.now(timezone.utc)

        if saved_at:
            age_hours = (now - saved_at).total_seconds() / 3600
            if age_hours < self._min_refresh_age_hours():
                return False, "token_too_young"

        if not expires_at:
            return False, "expiry_unknown"

        remaining = expires_at - now
        if remaining <= timedelta(days=self._refresh_threshold_days()):
            return True, "refresh_threshold"
        return False, "healthy"

    def ensure_fresh_instagram_token(self, force: bool = False) -> dict[str, Any]:
        self.sync_instagram_auth()

        should_refresh, reason = self._token_needs_refresh(force=force)
        if not should_refresh:
            return {
                "ok": True,
                "attempted": False,
                "reason": reason,
                "token_state": self._auth_state(),
            }

        refresh = refresh_instagram_long_lived_token(
            self.config,
            current_token=self.config.ig_token or "",
            current_user_id=self.config.ig_id,
        )

        render_sync = {"ok": False, "persisted": False, "skipped": True}
        if refresh.get("ok"):
            refreshed_token = refresh.get("token") or ((refresh.get("data") or {}).get("access_token"))
            if refreshed_token:
                render_sync = persist_instagram_token_to_render(
                    token=str(refreshed_token),
                    user_id=self.config.ig_id,
                )
            sync_instagram_token_sources(self.config, persist=False)

        return {
            "ok": bool(refresh.get("ok")),
            "attempted": True,
            "reason": reason,
            "refresh": refresh,
            "render_env_sync": render_sync,
            "token_state": self._auth_state(),
        }

    def _boot_sync(self) -> None:
        sync_instagram_token_sources(self.config, persist=False)
        try:
            self.ensure_fresh_instagram_token(force=False)
        except Exception:
            pass

    def sync_instagram_auth(self) -> dict:
        return sync_instagram_token_sources(self.config, persist=False)

    def snapshot(self) -> dict:
        sync = self.sync_instagram_auth()
        token_state = self._auth_state()
        return {
            "timestamp": datetime.now().isoformat(),
            "token_present": bool(self.config.ig_token),
            "ig_id_present": bool(self.config.ig_id),
            "render_url": self.config.render_url,
            "token_source": sync.get("token_source"),
            "user_id_source": sync.get("user_id_source"),
            "auth_path": sync.get("auth_path"),
            "enable_real_publish": self.config.enable_real_publish,
            "token_expires_at": token_state.get("expires_at"),
            "token_remaining_days": token_state.get("remaining_days"),
            "token_meta_source": token_state.get("source"),
            "render_env_sync_enabled": bool(os.environ.get("ACE_RENDER_API_KEY")),
        }

    def _load_font(self, size: int, bold: bool = False):
        if ImageFont is None:
            return None
        candidates = [
            "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for path in candidates:
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                continue
        try:
            return ImageFont.load_default()
        except Exception:
            return None

    def _draw_wrapped(self, draw, text: str, *, x: int, y: int, width: int, font, fill):
        lines = textwrap.wrap(text or "", width=width) or [""]
        line_height = getattr(font, "size", 22) + 14 if font else 28
        current_y = y
        for line in lines:
            draw.text((x, current_y), line, fill=fill, font=font)
            current_y += line_height
        return current_y

    def _build_test_image(self, *, headline: str, body: str, cta: str) -> str:
        self.config.media_dir.mkdir(parents=True, exist_ok=True)
        out = self.config.media_dir / f"ace_next_{uuid.uuid4().hex}.png"

        if Image is None or ImageDraw is None:
            out.write_bytes(
                bytes.fromhex(
                    "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4890000000D49444154789C63F8FFFFFF7F0009FB03FD2A86E38A0000000049454E44AE426082"
                )
            )
            return str(out)

        img = Image.new("RGB", (1080, 1350), (245, 244, 240))
        draw = ImageDraw.Draw(img)

        title_font = self._load_font(78, bold=True)
        body_font = self._load_font(42, bold=False)
        small_font = self._load_font(30, bold=False)
        brand_font = self._load_font(28, bold=True)

        draw.rectangle((0, 0, 1080, 220), fill=(18, 18, 22))
        draw.text((70, 78), "ACE Ω NEXT", fill=(255, 255, 255), font=brand_font)
        draw.text((850, 78), "@ace_next", fill=(180, 180, 188), font=small_font)

        draw.rounded_rectangle((55, 265, 1025, 1145), radius=34, fill=(255, 255, 255))
        draw.rectangle((82, 320, 98, 540), fill=(26, 92, 255))

        y = self._draw_wrapped(
            draw,
            headline,
            x=130,
            y=335,
            width=20,
            font=title_font,
            fill=(20, 20, 20),
        )

        y = self._draw_wrapped(
            draw,
            body,
            x=130,
            y=y + 45,
            width=32,
            font=body_font,
            fill=(55, 55, 60),
        )

        draw.text((130, 1060), cta, fill=(26, 92, 255), font=small_font)
        draw.text((130, 1110), "publicação de teste editorial", fill=(115, 115, 122), font=small_font)

        img.save(out)
        return str(out)

    def run(
        self,
        *,
        trend: str,
        force_placeholder: bool = False,
    ) -> dict:
        trend = (trend or "teste real").strip()
        plan = build_creative_plan(trend)

        style = plan.publish_style
        content_type = plan.publish_format_now
        caption = plan.caption

        refresh_result = self.ensure_fresh_instagram_token(force=False)

        media_path = None
        if not force_placeholder:
            media_path = self._build_test_image(
                headline=plan.headline,
                body=plan.body,
                cta=plan.cta,
            )

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
            "creative_plan": plan.to_dict(),
            "token_refresh": refresh_result,
            "runtime": self.snapshot(),
            "publish_result": publish_result,
            "last_publish": self.publish.last_publish(),
        }
