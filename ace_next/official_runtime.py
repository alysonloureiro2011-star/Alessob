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
)
from .visual_templates import resolve_visual_template

AUTH_STACK_IMPORT_ERROR: str | None = None

try:
    from .rubric_engine import evaluate_rubric_engine
    from .brand_veto_gate import evaluate_brand_veto_gate
    from .publication_authorization_gate import authorize_publication
except Exception as exc:  # boot-safe fallback
    AUTH_STACK_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
    evaluate_rubric_engine = None
    evaluate_brand_veto_gate = None
    authorize_publication = None


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
            "authorization_stack_import_error": AUTH_STACK_IMPORT_ERROR,
        }

    def _authorization_fallback(self, *, force_placeholder: bool, reason: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        rubric_engine = {
            "approved_minimum_quality": False,
            "eligible_for_brand_live": False,
            "global_score": 0.0,
            "global_score_100": 0,
            "breakdown": {},
            "floors": {},
            "failed_floors": ["authorization_stack_unavailable"],
            "reasons": [reason],
            "weights": {},
            "stack_ok": False,
        }
        brand_veto_gate = {
            "approved": False,
            "blocked": False,
            "categories": {
                "commodity": False,
                "cheap_ai": False,
                "template": False,
                "prototype": False,
                "brand_indignity": False,
            },
            "triggers": [],
            "reasons": [reason],
            "summary": "brand veto em fallback",
            "stack_ok": False,
        }
        publication_authorization_gate = {
            "selected_state": "technical_test" if force_placeholder else "internal_lab",
            "supported_states": [
                "technical_test",
                "internal_lab",
                "editorial_staging",
                "blocked_quality",
                "blocked_brand",
                "brand_live",
            ],
            "brand_live_allowed": False,
            "brand_live_blocked_by_default": True,
            "brand_live_candidate": False,
            "can_publish_placeholder": bool(force_placeholder),
            "can_publish_real": False,
            "block_reasons": [reason] if not force_placeholder else [],
            "reasons": [reason],
            "summary": "authorization stack em fallback seguro",
            "stack_ok": False,
        }
        return rubric_engine, brand_veto_gate, publication_authorization_gate

    def _run_authorization_stack(
        self,
        *,
        force_placeholder: bool,
        plan_dict: dict[str, Any],
        editorial_qa: dict[str, Any],
        visual_qa: dict[str, Any],
        perceptual_qa: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        if AUTH_STACK_IMPORT_ERROR or not evaluate_rubric_engine or not evaluate_brand_veto_gate or not authorize_publication:
            return self._authorization_fallback(
                force_placeholder=force_placeholder,
                reason=f"authorization_stack_import_error: {AUTH_STACK_IMPORT_ERROR or 'unknown'}",
            )

        try:
            rubric = evaluate_rubric_engine(
                plan=plan_dict,
                editorial_qa=editorial_qa,
                visual_qa=visual_qa,
                perceptual_qa=perceptual_qa,
            )
            brand_veto = evaluate_brand_veto_gate(
                plan=plan_dict,
                editorial_qa=editorial_qa,
                visual_qa=visual_qa,
                perceptual_qa=perceptual_qa,
                rubric=rubric,
            )
            authorization = authorize_publication(
                force_placeholder=force_placeholder,
                editorial_qa=editorial_qa,
                visual_qa=visual_qa,
                perceptual_qa=perceptual_qa,
                rubric=rubric,
                brand_veto=brand_veto,
            )

            rubric_dict = rubric.to_dict()
            rubric_dict["stack_ok"] = True

            brand_veto_dict = brand_veto.to_dict()
            brand_veto_dict["stack_ok"] = True

            authorization_dict = authorization.to_dict()
            authorization_dict["stack_ok"] = True

            return rubric_dict, brand_veto_dict, authorization_dict
        except Exception as exc:
            return self._authorization_fallback(
                force_placeholder=force_placeholder,
                reason=f"authorization_stack_runtime_error: {type(exc).__name__}: {exc}",
            )

    def run(
        self,
        *,
        trend: str,
        force_placeholder: bool = False,
    ) -> dict:
        trend = (trend or "teste real").strip()

        try:
            plan = build_creative_plan(trend)
            plan_dict = plan.to_dict()
        except Exception as exc:
            return {
                "ok": False,
                "operational_state": "blocked_quality",
                "brand_live_allowed": False,
                "block_reasons": [f"creative_planner_error: {type(exc).__name__}: {exc}"],
                "error": f"creative_planner_error: {type(exc).__name__}: {exc}",
                "runtime": self.snapshot(),
                "publish_result": None,
                "last_publish": self.publish.last_publish(),
            }

        try:
            editorial_qa_obj = evaluate_editorial_quality(plan_dict)
            editorial_qa = editorial_qa_obj.to_dict()
        except Exception as exc:
            editorial_qa = {
                "approved": False,
                "breakdown": {},
                "flags": [],
                "reasons": [f"editorial_qa_error: {type(exc).__name__}: {exc}"],
            }

        try:
            visual_identity = build_visual_identity(plan_dict)
            visual_identity_dict = visual_identity.to_dict()
        except Exception as exc:
            visual_identity = None
            visual_identity_dict = {"error": f"visual_identity_error: {type(exc).__name__}: {exc}"}

        try:
            typography = build_typography_spec(plan_dict)
            typography_dict = typography.to_dict()
        except Exception as exc:
            typography = None
            typography_dict = {"error": f"typography_error: {type(exc).__name__}: {exc}"}

        try:
            visual_contract = build_visual_contract(plan_dict)
            visual_contract_dict = visual_contract.to_dict()
        except Exception as exc:
            visual_contract = None
            visual_contract_dict = {"error": f"visual_contract_error: {type(exc).__name__}: {exc}"}

        try:
            visual_template = resolve_visual_template(plan_dict)
            visual_template_dict = visual_template.to_dict()
        except Exception as exc:
            visual_template = None
            visual_template_dict = {"error": f"visual_template_error: {type(exc).__name__}: {exc}"}

        try:
            if visual_identity is None or typography is None or visual_contract is None or visual_template is None:
                raise RuntimeError("visual dependencies unavailable")
            perceptual_qa_obj = evaluate_perceptual_quality(
                plan=plan_dict,
                contract=visual_contract,
                template=visual_template,
                identity=visual_identity,
                typography=typography,
            )
            perceptual_qa = perceptual_qa_obj.to_dict()
        except Exception as exc:
            perceptual_qa = {
                "approved": False,
                "final_score": 0,
                "breakdown": {},
                "metrics": {"zero_overlap": False},
                "reasons": [f"perceptual_qa_error: {type(exc).__name__}: {exc}"],
                "recommendations": [],
            }

        try:
            if visual_identity is None or typography is None:
                raise RuntimeError("visual identity/typography unavailable")
            visual_qa_obj = evaluate_visual_quality(
                plan=plan_dict,
                identity=visual_identity,
                typography=typography,
            )
            visual_qa = visual_qa_obj.to_dict()
        except Exception as exc:
            visual_qa = {
                "approved": False,
                "final_score": 0,
                "minimum_score": 75,
                "breakdown": {},
                "metrics": {"zero_overlap": False},
                "reasons": [f"visual_qa_error: {type(exc).__name__}: {exc}"],
                "recommendations": [],
            }

        rubric_engine, brand_veto_gate, publication_authorization_gate = self._run_authorization_stack(
            force_placeholder=force_placeholder,
            plan_dict=plan_dict,
            editorial_qa=editorial_qa,
            visual_qa=visual_qa,
            perceptual_qa=perceptual_qa,
        )

        try:
            carousel_preview = build_carousel_sequence(plan_dict)
        except Exception as exc:
            carousel_preview = {"ok": False, "error": f"carousel_preview_error: {type(exc).__name__}: {exc}"}

        try:
            stories_preview = build_stories_sequence(plan_dict)
        except Exception as exc:
            stories_preview = {"ok": False, "error": f"stories_preview_error: {type(exc).__name__}: {exc}"}

        try:
            refresh_result = self.ensure_fresh_instagram_token(force=False)
        except Exception as exc:
            refresh_result = {"ok": False, "error": f"token_refresh_error: {type(exc).__name__}: {exc}"}

        publish_result = None
        operational_state = publication_authorization_gate.get("selected_state", "internal_lab")
        brand_live_allowed = bool(publication_authorization_gate.get("brand_live_allowed", False))
        block_reasons = list(publication_authorization_gate.get("block_reasons") or [])

        try:
            if publication_authorization_gate.get("can_publish_placeholder"):
                publish_result = self.publish.publish_placeholder(
                    trend=trend,
                    style=str(plan.publish_style),
                    content_type=str(plan.publish_format_now),
                    caption=str(plan.caption),
                    media_path=None,
                )
            elif publication_authorization_gate.get("can_publish_real"):
                publish_result = self.publish.publish_real(
                    trend=trend,
                    style=str(plan.publish_style),
                    content_type=str(plan.publish_format_now),
                    caption=str(plan.caption),
                    media_path=None,
                )
        except Exception as exc:
            publish_result = {
                "ok": False,
                "error": f"publish_error: {type(exc).__name__}: {exc}",
            }
            block_reasons.append(f"publish_error: {type(exc).__name__}: {exc}")

        return {
            "ok": True,
            "mode": operational_state,
            "operational_state": operational_state,
            "brand_live_allowed": brand_live_allowed,
            "block_reasons": block_reasons,
            "trend": trend,
            "creative_plan": plan_dict,
            "editorial_qa": editorial_qa,
            "visual_contract": visual_contract_dict,
            "visual_template": visual_template_dict,
            "perceptual_qa": perceptual_qa,
            "visual_identity": visual_identity_dict,
            "typography": typography_dict,
            "visual_qa": visual_qa,
            "rubric_engine": rubric_engine,
            "brand_veto_gate": brand_veto_gate,
            "publication_authorization_gate": publication_authorization_gate,
            "carousel_preview": carousel_preview,
            "stories_preview": stories_preview,
            "token_refresh": refresh_result,
            "runtime": self.snapshot(),
            "publish_result": publish_result,
            "last_publish": self.publish.last_publish(),
        }
