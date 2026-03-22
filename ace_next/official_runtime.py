from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from .auth_store import load_instagram_auth, sync_instagram_token_sources
from .config import AceNextConfig
from .creative_planner import build_creative_plan
from .editorial_rubric import evaluate_editorial_quality
from .perceptual_qa import evaluate_perceptual_quality
from .publish import PublishService
from .render_env_sync import persist_instagram_token_to_render
from .token_upgrade import refresh_instagram_long_lived_token
from .visual_contract import build_visual_contract
from .visual_foundation_pack import (
    build_carousel_sequence,
    build_stories_sequence,
    build_typography_spec,
    build_visual_identity,
    evaluate_visual_quality,
    render_visual_foundation_card,
)
from .visual_templates import resolve_visual_template


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

    def run(
        self,
        *,
        trend: str,
        force_placeholder: bool = False,
    ) -> dict:
        trend = (trend or "teste real").strip()
        plan = build_creative_plan(trend)
        plan_dict = plan.to_dict()

        editorial_qa = evaluate_editorial_quality(plan_dict)

        visual_identity = build_visual_identity(plan_dict)
        typography = build_typography_spec(plan_dict)
        visual_contract = build_visual_contract(plan_dict)
        visual_template = resolve_visual_template(plan_dict)
        perceptual_qa = evaluate_perceptual_quality(
            plan=plan_dict,
            contract=visual_contract,
            template=visual_template,
            identity=visual_identity,
            typography=typography,
        )
        visual_qa = evaluate_visual_quality(
            plan=plan_dict,
            identity=visual_identity,
            typography=typography,
        )

        carousel_preview = build_carousel_sequence(plan_dict)
        stories_preview = build_stories_sequence(plan_dict)

        refresh_result = self.ensure_fresh_instagram_token(force=False)

        if (not editorial_qa.approved or not visual_qa.approved or not perceptual_qa.approved) and not force_placeholder:
            return {
                "ok": True,
                "mode": "blocked",
                "trend": trend,
                "creative_plan": plan_dict,
                "editorial_qa": editorial_qa.to_dict(),
                "visual_contract": visual_contract.to_dict(),
                "visual_template": visual_template.to_dict(),
                "perceptual_qa": perceptual_qa.to_dict(),
                "visual_identity": visual_identity.to_dict(),
                "typography": typography.to_dict(),
                "visual_qa": visual_qa.to_dict(),
                "carousel_preview": carousel_preview,
                "stories_preview": stories_preview,
                "token_refresh": refresh_result,
                "runtime": self.snapshot(),
                "publish_result": None,
                "last_publish": self.publish.last_publish(),
            }

        media_path = None
        if not force_placeholder:
            media_path = render_visual_foundation_card(
                config=self.config,
                plan=plan_dict,
                identity=visual_identity,
                typography=typography,
            )

        if force_placeholder:
            publish_result = self.publish.publish_placeholder(
                trend=trend,
                style=str(plan.publish_style),
                content_type=str(plan.publish_format_now),
                caption=str(plan.caption),
                media_path=media_path,
            )
            mode = "placeholder"
        else:
            publish_result = self.publish.publish_real(
                trend=trend,
                style=str(plan.publish_style),
                content_type=str(plan.publish_format_now),
                caption=str(plan.caption),
                media_path=media_path,
            )
            mode = "real" if publish_result.get("ok") else "error"

        return {
            "ok": True,
            "mode": mode,
            "trend": trend,
            "creative_plan": plan_dict,
            "editorial_qa": editorial_qa.to_dict(),
            "visual_contract": visual_contract.to_dict(),
            "visual_template": visual_template.to_dict(),
            "perceptual_qa": perceptual_qa.to_dict(),
            "visual_identity": visual_identity.to_dict(),
            "typography": typography.to_dict(),
            "visual_qa": visual_qa.to_dict(),
            "carousel_preview": carousel_preview,
            "stories_preview": stories_preview,
            "token_refresh": refresh_result,
            "runtime": self.snapshot(),
            "publish_result": publish_result,
            "last_publish": self.publish.last_publish(),
        }
