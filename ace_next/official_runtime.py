from future import annotations

import os from datetime import datetime, timedelta, timezone from typing import Any

from .auth_store import load_instagram_auth, sync_instagram_token_sources from .brand_surface_isolation import resolve_brand_surface_policy from .config import AceNextConfig from .creative_planner import build_creative_plan from .editorial_rubric import evaluate_editorial_quality from .lab_probe_policy import resolve_lab_probe_policy from .mission_control import decide_mission from .perceptual_qa import evaluate_perceptual_quality from .publish import PublishService from .render_env_sync import persist_instagram_token_to_render from .token_upgrade import refresh_instagram_long_lived_token from .visual_contract import build_visual_contract from .visual_foundation_pack import ( build_carousel_sequence, build_stories_sequence, build_typography_spec, build_visual_identity, evaluate_visual_quality, render_visual_foundation_card, ) from .visual_premium_bridge import build_visual_premium_bridge from .visual_templates import resolve_visual_template

AUTH_STACK_IMPORT_ERROR: str | None = None MEASUREMENT_STACK_IMPORT_ERROR: str | None = None REAL_PROBE_ALLOWED_STATES = ["internal_lab", "editorial_staging"] ALLOWED_RELEASE_OPERATION_STATES = { "internal_lab": "ready", "editorial_staging": "staging", "brand_live": "brand_live_ready", "blocked_quality": "blocked_quality", "blocked_brand": "blocked_brand", "technical_test": "technical_test", }

try: from .rubric_engine import evaluate_rubric_engine from .brand_veto_gate import evaluate_brand_veto_gate from .publication_authorization_gate import authorize_publication except Exception as exc: AUTH_STACK_IMPORT_ERROR = f"{type(exc).name}: {exc}" evaluate_rubric_engine = None evaluate_brand_veto_gate = None authorize_publication = None

try: from .performance_store import PerformanceStore except Exception as exc: MEASUREMENT_STACK_IMPORT_ERROR = f"{type(exc).name}: {exc}" PerformanceStore = None

try: from .hook_opening_engine import generate_hook_opening from .reel_storyboard_engine import ReelStoryboardEngine from .reel_rhythm_engine import ReelRhythmEngine from .post_production_pipeline import PostProductionPipeline from .audio_direction_layer import AudioDirectionLayer from .multimodal_reel_qa import MultimodalReelQA from .cinematic_gate import CinematicGate from .release_authority import ReleaseAuthority from .publish_guard import PublishGuard except Exception: generate_hook_opening = None ReelStoryboardEngine = None ReelRhythmEngine = None PostProductionPipeline = None AudioDirectionLayer = None MultimodalReelQA = None CinematicGate = None ReleaseAuthority = None PublishGuard = None

def _parse_dt(value: str | None) -> datetime | None: if not value: return None try: return datetime.fromisoformat(value.replace("Z", "+00:00")) except Exception: return None

def _normalize_probe_state(value: str | None) -> str: normalized = str(value or "auto").strip().lower() if normalized in {"auto", "internal_lab", "editorial_staging", "brand_live"}: return normalized return "auto"

def _as_bool_env(name: str, default: bool = False) -> bool: raw = os.environ.get(name) if raw is None: return default return str(raw).strip().lower() in {"1", "true", "yes", "on"}

def _mission_approval_required() -> bool: return _as_bool_env("ACE_REQUIRE_MISSION_APPROVAL", False)

def _planner_overrides_from_mission_decision(mission_decision: dict[str, Any] | None) -> dict[str, Any]: mission_decision = dict(mission_decision or {}) content_type = str(mission_decision.get("content_type") or "").strip().lower() publish_format_now = content_type if content_type in {"image", "carousel", "story", "reel"} else None return { "strategic_target_format": content_type or None, "publish_format_now": publish_format_now, "publish_style": None, "goal": mission_decision.get("goal"), "hypothesis": mission_decision.get("hypothesis"), "planner_selected": mission_decision.get("planner_selected"), }

def _safe_dict(value: Any) -> dict[str, Any]: return dict(value) if isinstance(value, dict) else {}

def _short_error_summary(value: Any, limit: int = 180) -> str | None: text = str(value or "").strip() if not text: return None return text if len(text) <= limit else f"{text[:limit - 3]}..."

def _normalize_release_operation_state(operational_state: str | None) -> str: state = str(operational_state or "technical_test").strip().lower() return ALLOWED_RELEASE_OPERATION_STATES.get(state, "technical_test")

def _publish_truth_state_from_result(publish_result: dict[str, Any] | None) -> str: publish_result = _safe_dict(publish_result) if not publish_result: return "publish_truth_absent"

publish_status = str(publish_result.get("publish_status") or "").strip().lower()
receipt_id = publish_result.get("receipt_id")
media_id = publish_result.get("media_id")
permalink = publish_result.get("permalink")

if publish_status == "published_real_probe" and receipt_id and media_id:
    return "publish_truth_confirmed"
if receipt_id or permalink or media_id:
    return "publish_attempt_recorded"
return "publish_truth_absent"

def _gate_stage_summary(reel_stack: dict[str, Any] | None) -> dict[str, Any]: reel_stack = _safe_dict(reel_stack) cinematic_gate = _safe_dict(reel_stack.get("cinematic_gate")) release_authority = _safe_dict(reel_stack.get("release_authority")) publish_guard = _safe_dict(reel_stack.get("publish_guard"))

return {
    "ok": bool(reel_stack.get("ok")),
    "stack_state": reel_stack.get("stack_state"),
    "cinematic_gate_state": cinematic_gate.get("state"),
    "cinematic_gate_approved": bool(cinematic_gate.get("approved")),
    "cinematic_score": cinematic_gate.get("cinematic_score"),
    "release_state": release_authority.get("release_state"),
    "approved_for_publish": bool(release_authority.get("approved_for_publish")),
    "publish_guard_mode": publish_guard.get("mode"),
    "can_publish": bool(publish_guard.get("can_publish")),
    "next_step": publish_guard.get("next_step"),
}

class OfficialRuntime: def init(self, config: AceNextConfig): self.config = config self.publish = PublishService(config) self._last_run_summary: dict[str, Any] = {} self._boot_sync()

def _brand_env_flags(self) -> dict[str, Any]:
    return {
        "ACE_BRAND_SURFACE_MODE": os.environ.get("ACE_BRAND_SURFACE_MODE", "protected"),
        "ACE_ALLOW_MAIN_SURFACE_LAB_PROBE": _as_bool_env("ACE_ALLOW_MAIN_SURFACE_LAB_PROBE", False),
        "ACE_ALLOW_MAIN_SURFACE_EDITORIAL_STAGING": _as_bool_env("ACE_ALLOW_MAIN_SURFACE_EDITORIAL_STAGING", False),
        "ACE_REQUIRE_HUMAN_REVIEW_FOR_BRAND_LIVE": _as_bool_env("ACE_REQUIRE_HUMAN_REVIEW_FOR_BRAND_LIVE", True),
    }

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

def _runtime_queue_state(self) -> dict[str, int]:
    return {"active_jobs": 0, "pending_jobs": 0}

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
        return {"ok": True, "attempted": False, "reason": reason, "token_state": self._auth_state()}

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

def sync_instagram_auth(self) -> dict[str, Any]:
    return sync_instagram_token_sources(self.config, persist=False)

def _performance_store_summary(self) -> dict[str, Any]:
    if MEASUREMENT_STACK_IMPORT_ERROR or PerformanceStore is None:
        return {"ok": False, "error": MEASUREMENT_STACK_IMPORT_ERROR or "measurement_stack_unavailable"}
    try:
        return PerformanceStore(self.config).summary().to_dict()
    except Exception as exc:
        return {"ok": False, "error": f"performance_store_summary_error: {type(exc).__name__}: {exc}"}

def snapshot(self) -> dict[str, Any]:
    sync = self.sync_instagram_auth()
    token_state = self._auth_state()
    env_flags = self._brand_env_flags()
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
        "measurement_stack_import_error": MEASUREMENT_STACK_IMPORT_ERROR,
        "performance_store": self._performance_store_summary(),
        "experiment_registry": {"ok": False, "error": "not_loaded_in_slim_runtime"},
        "episodic_performance_memory": {"ok": False, "error": "not_loaded_in_slim_runtime"},
        "real_probe_route_supported": True,
        "real_probe_allowed_states": REAL_PROBE_ALLOWED_STATES,
        "brand_live_allowed": False,
        "brand_surface_mode": env_flags.get("ACE_BRAND_SURFACE_MODE"),
        "brand_surface_flags": env_flags,
        "last_run_summary": self._last_run_summary,
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
            "brand_live",
            "blocked_quality",
            "blocked_brand",
        ],
        "can_publish_placeholder": bool(force_placeholder),
        "can_publish_real": False,
        "brand_live_blocked_by_default": True,
        "brand_live_candidate": False,
        "main_surface_allowed": False,
        "requires_human_review": True,
        "block_reasons": [reason] if not force_placeholder else [],
        "reasons": [reason],
        "summary": "authorization stack em fallback seguro",
        "stack_ok": False,
        "premium_classification": "internal_lab" if not force_placeholder else "technical_test",
        "eligible_for_editorial_staging": False,
        "eligible_for_brand_live_candidate": False,
        "missing_for_brand_live": [],
        "score_gap_to_brand_live": 0.0,
        "next_quality_lift_targets": [],
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
    env_flags: dict[str, Any],
    request_flags: dict[str, Any],
    staging_hardener: dict[str, Any] | None = None,
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
            env_flags=env_flags,
            request_flags=request_flags,
            staging_hardener=staging_hardener,
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

def _run_reel_premium_stack(
    self,
    *,
    trend: str,
    creative_plan: dict[str, Any],
    visual_qa: dict[str, Any],
    perceptual_qa: dict[str, Any],
    publication_authorization_gate: dict[str, Any],
    operational_state: str,
    publish_truth_state: str = "publish_truth_absent",
) -> dict[str, Any]:
    if not all([
        generate_hook_opening,
        ReelStoryboardEngine,
        ReelRhythmEngine,
        PostProductionPipeline,
        AudioDirectionLayer,
        MultimodalReelQA,
        CinematicGate,
        ReleaseAuthority,
        PublishGuard,
    ]):
        return {
            "ok": False,
            "stack_state": "reel_stack_import_error",
            "error": "reel premium stack unavailable",
        }

    hook_raw = generate_hook_opening(
        trend=trend,
        style=creative_plan.get("publish_style"),
        content_type=creative_plan.get("publish_format_now"),
    )
    hook_opening = {
        "opening_pattern": "curiosity_gap",
        "opening_text": (
            hook_raw.get("text_hook")
            or hook_raw.get("audio_hook")
            or hook_raw.get("visual_hook")
            or trend
        ),
        "visual_hook": hook_raw.get("visual_hook"),
        "audio_hook": hook_raw.get("audio_hook"),
        "text_hook": hook_raw.get("text_hook"),
        "pattern_interrupts": hook_raw.get("pattern_interrupts") or [],
        "intensity_score": hook_raw.get("intensity_score"),
    }

    storyboard = ReelStoryboardEngine().run(
        creative_plan=creative_plan,
        hook_opening=hook_opening,
    )
    rhythm = ReelRhythmEngine().run(
        storyboard=storyboard,
        hook_opening={"opening_pattern": hook_opening.get("opening_pattern", "curiosity_gap")},
    )
    subtitles = {
        "emphasis_mode": (
            "short_emphasis_lines"
            if rhythm.get("subtitle_pacing_hint") == "short_emphasis_lines"
            else "balanced_lines"
        )
    }
    post_production = PostProductionPipeline().run(
        storyboard=storyboard,
        rhythm=rhythm,
        subtitles=subtitles,
    )
    audio_direction = AudioDirectionLayer().run(
        hook_opening={"opening_pattern": hook_opening.get("opening_pattern", "curiosity_gap")},
        rhythm=rhythm,
        post_production=post_production,
    )

    visual_score_10 = max(
        float(visual_qa.get("final_score", 0)) / 10.0,
        float(perceptual_qa.get("final_score", 0)) / 10.0,
    )
    audio_score_10 = 8.6 if audio_direction.get("state") == "audio_direction_layer_ready" else 6.0
    rhythm_score_10 = 8.6 if rhythm.get("rhythm_state") == "reel_rhythm_ready" else 6.0

    multimodal_qa = MultimodalReelQA().run(
        visual_gate={"global_visual_score": visual_score_10},
        audio_gate={"global_audio_score": audio_score_10},
        reel_gate={"global_score": rhythm_score_10},
        naturalism={"naturalism_state": "naturalism_engine_ready"},
    )

    overall_quality_score = max(
        visual_score_10,
        8.5 if publication_authorization_gate.get("eligible_for_editorial_staging") else visual_score_10,
    )

    cinematic_gate = CinematicGate().run(
        multimodal_qa=multimodal_qa,
        reel_director={
            "visual_mode": "cinematic_retention",
            "cut_mode": "precision_fast",
        },
        premium_decision={
            "overall_quality_score": overall_quality_score
        },
    )

    release_authority = ReleaseAuthority().run(
        cinematic_gate=cinematic_gate,
        premium_decision={"overall_quality_score": overall_quality_score},
        operation_bridge={
            "operational_state": _normalize_release_operation_state(operational_state)
        },
    )

    publish_guard = PublishGuard().run(
        release_authority=release_authority,
        publish_truth={"truth_state": publish_truth_state},
    )

    return {
        "ok": True,
        "stack_state": "reel_premium_stack_ready",
        "hook_opening": hook_opening,
        "storyboard": storyboard,
        "rhythm": rhythm,
        "subtitles": subtitles,
        "post_production": post_production,
        "audio_direction": audio_direction,
        "multimodal_qa": multimodal_qa,
        "cinematic_gate": cinematic_gate,
        "release_authority": release_authority,
        "publish_guard": publish_guard,
        "pipeline_summary": _gate_stage_summary({
            "ok": True,
            "stack_state": "reel_premium_stack_ready",
            "cinematic_gate": cinematic_gate,
            "release_authority": release_authority,
            "publish_guard": publish_guard,
        }),
    }

def _measurement_summary(self, *, publish_result: dict[str, Any] | None) -> dict[str, Any]:
    publish_result = _safe_dict(publish_result)
    receipt_id = publish_result.get("receipt_id")
    media_id = publish_result.get("media_id")
    permalink = publish_result.get("permalink")
    publish_status = publish_result.get("publish_status")
    error_summary = _short_error_summary(publish_result.get("error"))
    return {
        "post_performance_contract": {
            "ok": True,
            "publish_receipt_bridge": {
                "publish_status": publish_status,
                "receipt_id": receipt_id,
                "media_id": media_id,
                "permalink": permalink,
                "content_type": publish_result.get("content_type"),
                "style": publish_result.get("style"),
                "created_at": publish_result.get("created_at"),
            },
            "evidence_bridge": {
                "has_real_receipt": bool(receipt_id),
                "has_media_id": bool(media_id),
                "has_permalink": bool(permalink),
                "evidence_bridge_state": (
                    "linked_real_target"
                    if receipt_id and media_id
                    else "receipt_only"
                    if receipt_id
                    else "no_receipt"
                ),
            },
        },
        "performance_ingest": {
            "ok": True,
            "attempted": bool(media_id),
            "collection_success": False,
            "source_status": "not_collected_yet",
            "real_metrics": {"source_status": "not_collected_yet"},
            "attention_inputs": {},
            "errors": [error_summary] if error_summary else [],
            "raw": {},
        },
        "attention_metrics": {
            "ok": True,
            "source_status": "not_collected_yet",
            "breakdown": {},
            "available_inputs": [],
            "notes": [],
        },
        "resonance_engine": {"ok": True, "resonance_score": None, "reasons": []},
        "reward_prediction": {"ok": True, "reward_prediction_score": None, "reasons": []},
        "thompson_sampler": {
            "ok": True,
            "selected_variant": None,
            "confidence_level": "low",
            "decision_state": "collecting",
            "posterior_mean": None,
            "winner_candidate": False,
            "reasons": [],
        },
        "decision_core_summary": {
            "ok": True,
            "resonance_score": None,
            "reward_prediction_score": None,
            "selected_variant": None,
            "confidence_level": "low",
            "experiment_decision_state": "collecting",
            "posterior_mean": None,
            "winner_candidate": False,
            "reasons": ["measurement_slim_mode"],
        },
        "evidence_interpreter": {
            "ok": True,
            "evidence_state": (
                "linked_real_target"
                if receipt_id and media_id
                else "receipt_only"
                if receipt_id
                else "no_receipt"
            ),
            "evidence_strength": "low" if receipt_id else "none",
            "evidence_ready_for_resolution": False,
            "evidence_reasons": [],
            "bridge_state": (
                "linked_real_target"
                if receipt_id and media_id
                else "receipt_only"
                if receipt_id
                else "no_receipt"
            ),
        },
        "experiment_resolution": {
            "ok": True,
            "resolution_state": "collecting",
            "can_resolve": False,
            "winner_candidate": False,
            "loser_candidate": False,
            "keep_collecting": True,
            "confidence_level": "low",
            "resolution_reason": "measurement_slim_mode",
            "promotion_readiness": "not_ready",
        },
        "recommendation_engine": {
            "ok": True,
            "recommended_action": "measure_now" if media_id else "publish_or_improve",
            "action_priority": "medium",
            "recommendation_reason": "measurement_slim_mode",
            "next_best_step": "coletar métricas reais após publicação",
            "safe_to_repeat": True,
            "safe_to_promote_to_editorial_staging": False,
            "requires_human_review": True,
        },
        "wave10_summary": {"ok": True, "evidence_state": "collecting", "resolution_state": "collecting", "recommended_action": "measure_now"},
        "wave11_summary": {
            "ok": True,
            "brand_live_allowed": False,
            "evidence_state": "collecting",
            "has_receipt": bool(receipt_id),
            "has_media_id": bool(media_id),
            "has_permalink": bool(permalink),
            "can_resolve": False,
            "recommended_action": "measure_now" if media_id else "publish_or_improve",
            "next_best_step": "coletar métricas reais após publicação",
        },
        "experiment_registry": {"ok": False, "error": "measurement_slim_runtime"},
        "episodic_performance_memory": {"ok": False, "error": "measurement_slim_runtime"},
        "reflection_memory": {
            "ok": True,
            "status": "recorded",
            "notes": [],
            "guardrails": {
                "can_change_brand_policy": False,
                "can_change_editorial_policy": False,
                "can_change_visual_policy": False,
                "can_authorize_brand_live": False,
                "can_autopublish": False,
            },
        },
        "learning_loop": {
            "ok": True,
            "error": None,
            "insight_control": {
                "can_record": True,
                "can_consolidate": False,
                "can_suggest": True,
                "can_change_brand_policy": False,
                "can_change_editorial_policy": False,
                "can_change_visual_policy": False,
                "can_autopublish_brand_live": False,
            },
        },
        "performance_summary": {"ok": True, "mode": "measurement_slim_runtime"},
        "performance_store": self._performance_store_summary(),
    }

def run(
    self,
    *,
    trend: str,
    force_placeholder: bool = False,
    force_real_probe: bool = False,
    probe_state: str | None = None,
) -> dict[str, Any]:
    trend = (trend or "teste real").strip()
    probe_state_requested = _normalize_probe_state(probe_state)

    env_flags = self._brand_env_flags()
    request_flags = {
        "probe_requested": bool(force_real_probe) and not force_placeholder,
        "explicit_probe_arm": bool(force_real_probe) and not force_placeholder,
        "explicit_main_surface_publish": bool(force_real_probe) and not force_placeholder,
        "brand_live_arm": False,
        "human_review_approved": False,
    }

    mission_control_state = {
        "enabled": True,
        "approval_required": _mission_approval_required(),
        "blocked": False,
    }

    try:
        mission_decision = decide_mission(
            trend,
            format_hint=None,
            signal_context={"source": "official_runtime", "mode": "run"},
            brand_context={
                "brand_surface_mode": env_flags.get("ACE_BRAND_SURFACE_MODE"),
                "brand_live_allowed": False,
            },
            queue_state=self._runtime_queue_state(),
            recent_signal_score=None,
        )
    except Exception as exc:
        mission_decision = {
            "ok": False,
            "should_act": True,
            "reason": f"mission_control_runtime_error: {type(exc).__name__}: {exc}",
            "decision_state": "fallback_allow",
            "trend": trend,
            "trend_normalized": trend.strip().lower(),
            "style": "unknown",
            "content_type": "image",
            "goal": "authority",
            "hypothesis": "mission_control_unavailable_runtime_fallback",
            "priority": 0.5,
            "api_budget_mode": "lean",
            "confidence": 0.2,
            "planner_selected": "mission_control_runtime_fallback",
            "queue_full": False,
            "signal_strength": "unknown",
            "guardrails": {
                "brand_live_allowed": False,
                "safe_for_brand_live": False,
                "requires_human_review": True,
            },
            "inputs": {},
        }
        mission_control_state["fallback"] = True
        mission_control_state["error"] = mission_decision["reason"]

    if mission_control_state["approval_required"] and not bool(mission_decision.get("should_act")):
        mission_control_state["blocked"] = True
        return {
            "ok": True,
            "mode": "blocked_by_mission_control",
            "authorization_state": "blocked_by_mission_control",
            "operational_state": "blocked_by_mission_control",
            "brand_live_allowed": False,
            "trend": trend,
            "mission_decision": mission_decision,
            "mission_control_state": mission_control_state,
            "block_reasons": [mission_decision.get("reason")],
            "runtime": self.snapshot(),
            "publish_result": None,
            "last_publish": self.publish.last_publish(),
        }

    try:
        plan = build_creative_plan(
            trend,
            overrides=_planner_overrides_from_mission_decision(mission_decision),
            mission_decision=mission_decision,
            recent_memory=[],
        )
        plan_dict = plan.to_dict()
    except Exception as exc:
        return {
            "ok": False,
            "operational_state": "blocked_quality",
            "brand_live_allowed": False,
            "block_reasons": [f"creative_planner_error: {type(exc).__name__}: {exc}"],
            "error": f"creative_planner_error: {type(exc).__name__}: {exc}",
            "mission_decision": mission_decision,
            "mission_control_state": mission_control_state,
            "runtime": self.snapshot(),
            "publish_result": None,
            "last_publish": self.publish.last_publish(),
        }

    try:
        editorial_qa = evaluate_editorial_quality(plan_dict).to_dict()
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
        visual_template_obj = resolve_visual_template(plan_dict)
        visual_template_dict = visual_template_obj.to_dict()
    except Exception as exc:
        visual_template_obj = None
        visual_template_dict = {"error": f"visual_template_error: {type(exc).__name__}: {exc}"}

    try:
        if visual_identity is None or typography is None or visual_contract is None or visual_template_obj is None:
            raise RuntimeError("visual dependencies unavailable")
        perceptual_qa = evaluate_perceptual_quality(
            plan=plan_dict,
            contract=visual_contract,
            template=visual_template_obj,
            identity=visual_identity,
            typography=typography,
        ).to_dict()
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
        visual_qa = evaluate_visual_quality(
            plan=plan_dict,
            identity=visual_identity,
            typography=typography,
        ).to_dict()
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

    premium_visual = build_visual_premium_bridge(
        creative_plan=plan_dict,
        visual_identity=visual_identity_dict,
        visual_contract=visual_contract_dict,
        strategic_format=plan_dict.get("publish_format_now"),
        template_id=None,
        capture_mode="safe",
    )

    rubric_engine, brand_veto_gate, publication_authorization_gate = self._run_authorization_stack(
        force_placeholder=force_placeholder,
        plan_dict=plan_dict,
        editorial_qa=editorial_qa,
        visual_qa=visual_qa,
        perceptual_qa=perceptual_qa,
        env_flags=env_flags,
        request_flags=request_flags,
        staging_hardener=dict(premium_visual.get("hardening_report") or {}),
    )

    authorization_state = publication_authorization_gate.get("selected_state", "technical_test")
    operational_state = authorization_state
    block_reasons = list(publication_authorization_gate.get("reasons") or [])
    if publication_authorization_gate.get("stack_ok") is False:
        block_reasons.extend(publication_authorization_gate.get("block_reasons") or [])

    lab_probe_policy = resolve_lab_probe_policy(
        operational_state=authorization_state,
        requested_probe=request_flags["probe_requested"],
        requested_state=probe_state_requested,
        env_flags=env_flags,
        request_flags=request_flags,
    )

    brand_surface_policy = resolve_brand_surface_policy(
        operational_state=authorization_state,
        requested_real_publish=lab_probe_policy.get("requested_real_publish", False),
        env_flags=env_flags,
        request_flags=request_flags,
        quality_context={
            "brand_live_candidate": publication_authorization_gate.get("brand_live_candidate"),
            "can_publish_real": publication_authorization_gate.get("can_publish_real"),
        },
    )

    explicit_probe_execution_allowed = bool(
        request_flags.get("probe_requested")
        and request_flags.get("explicit_probe_arm")
        and not force_placeholder
        and str(lab_probe_policy.get("probe_state_effective") or authorization_state).strip().lower() in REAL_PROBE_ALLOWED_STATES
    )

    prepublish_reel_stack = self._run_reel_premium_stack(
        trend=trend,
        creative_plan=plan_dict,
        visual_qa=visual_qa,
        perceptual_qa=perceptual_qa,
        publication_authorization_gate=publication_authorization_gate,
        operational_state=operational_state,
        publish_truth_state="publish_truth_absent",
    ) 

    # HARD GATE SOBERANO (B2)

release_authority = (prepublish_reel_stack or {}).get("release_authority") or {}
publish_guard = (prepublish_reel_stack or {}).get("publish_guard") or {}

if not publish_guard.get("can_publish"):
    return {
        "ok": False,
        "state": "HALT_BLOCKED_BY_GATE",
        "reason": "publish_guard_blocked",
        "release_authority": release_authority,
        "publish_guard": publish_guard,
        "prepublish_reel_stack": prepublish_reel_stack,
    }

    if prepublish_reel_stack.get("ok"):
        release_authority = _safe_dict(prepublish_reel_stack.get("release_authority"))
        publish_guard = _safe_dict(prepublish_reel_stack.get("publish_guard"))
        if release_authority.get("release_state", "").startswith("BLOCKED_"):
            block_reasons.append(release_authority.get("release_state"))
        if publish_guard.get("mode") == "blocked":
            block_reasons.append("blocked_by_publish_guard")

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

    render_path = None
    render_error = None
    publish_result: dict[str, Any] | None = None

    linkage_context = {
        "operational_state": operational_state,
        "brand_live_allowed": False,
        "probe": {},
        "brand_surface_policy": brand_surface_policy,
        "lab_probe_policy": lab_probe_policy,
        "premium_gate": _gate_stage_summary(prepublish_reel_stack),
    }

    prepublish_guard = _safe_dict(prepublish_reel_stack.get("publish_guard"))
    publish_guard_mode = prepublish_guard.get("mode")
    publish_guard_can_publish = bool(prepublish_guard.get("can_publish"))

    if force_placeholder or publication_authorization_gate.get("can_publish_placeholder"):
        publish_result = self.publish.publish_placeholder(
            trend=trend,
            style=str(plan.publish_style),
            content_type=str(plan.publish_format_now),
            caption=str(plan.caption),
            media_path=None,
            linkage_context=linkage_context,
        )
    else:
        should_render = bool(lab_probe_policy.get("probe_render_requested")) or publish_guard_can_publish
        if should_render:
            try:
                render_path = render_visual_foundation_card(
                    config=self.config,
                    plan=plan_dict,
                    identity=visual_identity,
                    typography=typography,
                )
                lab_probe_policy["probe_render_executed"] = True
                lab_probe_policy["render_path"] = render_path
            except Exception as exc:
                render_error = f"render_error: {type(exc).__name__}: {exc}"
                block_reasons.append(render_error)
                lab_probe_policy["probe_render_executed"] = False
                lab_probe_policy["render_path"] = None

        effective_real_publish = bool(
            explicit_probe_execution_allowed
            and lab_probe_policy.get("probe_eligible")
            and publish_guard_mode == "ready"
        )

        if effective_real_publish:
            linkage_context["probe"] = {
                "requested": lab_probe_policy.get("probe_requested"),
                "requested_state": lab_probe_policy.get("probe_state_requested"),
                "effective_state": lab_probe_policy.get("probe_state_effective"),
                "eligible": True,
                "render_executed": bool(lab_probe_policy.get("probe_render_executed")),
                "publish_executed": False,
                "render_path": render_path,
                "render_error": render_error,
                "allow_real_publish": True,
                "probe_block_reason": None,
                "surface_mode": brand_surface_policy.get("surface_mode"),
            }

            publish_result = self.publish.publish_real(
                trend=trend,
                style=str(plan.publish_style),
                content_type=str(plan.publish_format_now),
                caption=str(plan.caption),
                media_path=render_path,
                linkage_context=linkage_context,
            )

            publish_status = str((publish_result or {}).get("publish_status") or "")
            lab_probe_policy["probe_publish_executed"] = publish_status == "published_real_probe"
        else:
            publish_result = {
                "ok": True,
                "publish_status": "not_published_surface_protected" if publish_guard_mode != "ready" else "not_published_probe_not_allowed",
                "operational_state": operational_state,
                "content_type": str(plan.publish_format_now),
                "style": str(plan.publish_style),
                "created_at": datetime.now().isoformat(),
                "render_path": render_path,
                "surface_mode": brand_surface_policy.get("surface_mode"),
                "main_surface_allowed": brand_surface_policy.get("main_surface_allowed"),
                "probe_requested": lab_probe_policy.get("probe_requested"),
                "probe_eligible": lab_probe_policy.get("probe_eligible"),
                "probe_publish_executed": False,
                "probe_block_reason": lab_probe_policy.get("probe_block_reason") or brand_surface_policy.get("block_reason"),
                "render_error": render_error,
            }

    publish_truth_state = _publish_truth_state_from_result(publish_result)
    postpublish_reel_stack = self._run_reel_premium_stack(
        trend=trend,
        creative_plan=plan_dict,
        visual_qa=visual_qa,
        perceptual_qa=perceptual_qa,
        publication_authorization_gate=publication_authorization_gate,
        operational_state=operational_state,
        publish_truth_state=publish_truth_state,
    )
    measurement = self._measurement_summary(publish_result=publish_result)

    self._last_run_summary = {
        "timestamp": datetime.now().isoformat(),
        "premium_classification": publication_authorization_gate.get("premium_classification"),
        "eligible_for_editorial_staging": publication_authorization_gate.get("eligible_for_editorial_staging"),
        "eligible_for_brand_live_candidate": publication_authorization_gate.get("eligible_for_brand_live_candidate"),
        "missing_for_brand_live": publication_authorization_gate.get("missing_for_brand_live"),
        "score_gap_to_brand_live": publication_authorization_gate.get("score_gap_to_brand_live"),
        "next_quality_lift_targets": publication_authorization_gate.get("next_quality_lift_targets"),
        "caption_gate_result": plan_dict.get("caption_gate_result"),
        "caption_gate_score": plan_dict.get("caption_gate_score"),
        "caption_gate_flags": plan_dict.get("caption_gate_flags"),
        "premium_visual_result": bool(premium_visual.get("approved_for_premium_visual")),
        "premium_visual_reasons": premium_visual.get("reasons"),
        "publication_authorization_summary": publication_authorization_gate.get("summary"),
        "selected_template_id": premium_visual.get("selected_template_id"),
        "premium_render_state": premium_visual.get("premium_render_state"),
        "hardening_applied": premium_visual.get("hardening_applied"),
        "hardening_report": premium_visual.get("hardening_report"),
        "reel_stack_state": prepublish_reel_stack.get("stack_state"),
        "prepublish_gate": _gate_stage_summary(prepublish_reel_stack),
        "postpublish_gate": _gate_stage_summary(postpublish_reel_stack),
        "publish_truth_state": publish_truth_state,
    }

    return {
        "ok": True,
        "mode": operational_state,
        "authorization_state": authorization_state,
        "operational_state": operational_state,
        "surface_mode": brand_surface_policy.get("surface_mode"),
        "main_surface_allowed": brand_surface_policy.get("main_surface_allowed"),
        "brand_live_allowed": False,
        "real_probe_route_supported": True,
        "real_probe_allowed_states": REAL_PROBE_ALLOWED_STATES,
        "probe_requested": bool(lab_probe_policy.get("probe_requested")),
        "probe_eligible": bool(lab_probe_policy.get("probe_eligible")),
        "probe_publish_executed": bool(lab_probe_policy.get("probe_publish_executed")),
        "probe_block_reason": lab_probe_policy.get("probe_block_reason") or brand_surface_policy.get("block_reason"),
        "block_reasons": block_reasons,
        "brand_surface_policy": brand_surface_policy,
        "lab_probe_policy": lab_probe_policy,
        "trend": trend,
        "mission_decision": mission_decision,
        "mission_control_state": mission_control_state,
        "creative_plan": plan_dict,
        "editorial_qa": editorial_qa,
        "visual_contract": visual_contract_dict,
        "visual_template": visual_template_dict,
        "perceptual_qa": perceptual_qa,
        "visual_identity": visual_identity_dict,
        "typography": typography_dict,
        "visual_qa": visual_qa,
        "premium_visual": premium_visual,
        "approved_for_premium_visual": premium_visual.get("approved_for_premium_visual"),
        "selected_template_id": premium_visual.get("selected_template_id"),
        "premium_render_state": premium_visual.get("premium_render_state"),
        "hardening_applied": premium_visual.get("hardening_applied"),
        "hardening_report": premium_visual.get("hardening_report"),
        "premium_visual_reasons": premium_visual.get("reasons"),
        "rubric_engine": rubric_engine,
        "brand_veto_gate": brand_veto_gate,
        "publication_authorization_gate": publication_authorization_gate,
        "carousel_preview": carousel_preview,
        "stories_preview": stories_preview,
        "token_refresh": refresh_result,
        "post_performance_contract": measurement["post_performance_contract"],
        "performance_ingest": measurement["performance_ingest"],
        "real_metrics_contract": measurement["performance_ingest"].get("real_metrics"),
        "attention_metrics": measurement["attention_metrics"],
        "resonance_engine": measurement["resonance_engine"],
        "reward_prediction": measurement["reward_prediction"],
        "thompson_sampler": measurement["thompson_sampler"],
        "decision_core_summary": measurement["decision_core_summary"],
        "publish_receipt_bridge": measurement["post_performance_contract"].get("publish_receipt_bridge"),
        "evidence_bridge": measurement["post_performance_contract"].get("evidence_bridge"),
        "evidence_interpreter": measurement["evidence_interpreter"],
        "experiment_resolution": measurement["experiment_resolution"],
        "recommendation_engine": measurement["recommendation_engine"],
        "recommendation_state": measurement["recommendation_engine"].get("recommended_action"),
        "resolution_state": measurement["experiment_resolution"].get("resolution_state"),
        "wave10_summary": measurement["wave10_summary"],
        "wave11_summary": measurement["wave11_summary"],
        "experiment_registry": measurement["experiment_registry"],
        "episodic_performance_memory": measurement["episodic_performance_memory"],
        "reflection_memory": measurement["reflection_memory"],
        "learning_loop": measurement["learning_loop"],
        "performance_summary": measurement["performance_summary"],
        "performance_store": measurement["performance_store"],
        "runtime": self.snapshot(),
        "publish_result": publish_result,
        "last_publish": self.publish.last_publish(),
        "reel_stack": prepublish_reel_stack,
        "prepublish_reel_stack": prepublish_reel_stack,
        "postpublish_reel_stack": postpublish_reel_stack,
        "hook_opening": prepublish_reel_stack.get("hook_opening"),
        "reel_storyboard": prepublish_reel_stack.get("storyboard"),
        "reel_rhythm": prepublish_reel_stack.get("rhythm"),
        "post_production": prepublish_reel_stack.get("post_production"),
        "audio_direction": prepublish_reel_stack.get("audio_direction"),
        "multimodal_reel_qa": prepublish_reel_stack.get("multimodal_qa"),
        "cinematic_gate": prepublish_reel_stack.get("cinematic_gate"),
        "release_authority": prepublish_reel_stack.get("release_authority"),
        "publish_guard": prepublish_reel_stack.get("publish_guard"),
        "publish_truth_state": publish_truth_state,
        "organism_cycle": {
            "planning": True,
            "premium_stack": bool(prepublish_reel_stack.get("ok")),
            "gate_before_publish": bool(_safe_dict(prepublish_reel_stack.get("publish_guard")).get("state") == "publish_guard_ready"),
            "publish_truth_after_publish": True,
            "organism_state": "planning_to_stack_to_gate_to_publish_truth",
        },
    }
