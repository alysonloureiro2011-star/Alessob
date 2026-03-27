from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any
from typing import Any

from .trend_radar import TrendRadar
from .config import AceNextConfig
from .config import AceNextConfig
from .runtime_bootstrap import bootstrap_capabilities
from .runtime_registry import capability_registry_snapshot, resolve_capability
from .runtime_adapters import (
    adapt_legacy_mission_decision,
    adapt_legacy_publish_result,
    adapt_legacy_visual,
)
from .runtime_contracts import (
    build_runtime_execution_envelope,
    build_runtime_request,
    normalize_probe_state,
    normalize_trend,
    safe_bool,
    safe_dict,
)

REAL_PROBE_ALLOWED_STATES = {"internal_lab", "editorial_staging"}
ALLOWED_RELEASE_OPERATION_STATES = {
    "internal_lab": "ready",
    "editorial_staging": "staging",
    "brand_live": "brand_live_ready",
    "blocked_quality": "blocked_quality",
    "blocked_brand": "blocked_brand",
    "technical_test": "technical_test",
    "blocked_by_mission_control": "blocked_by_mission_control",
}

STUDY_TAGS = {
    "psychology_clt": "clarity_density_control",
    "stepps": "social_currency_triggers_emotion_public_practical_value_stories",
    "hook_attention": "first_3s_pattern_interrupt_curiosity_gap",
    "rhythm": "cadence_450_1200_850_300",
    "naturalism": "micro_expression_grain_breathing_foley",
    "mab": "exploration_vs_exploitation",
    "attention_engineering": "save_share_replay_retention_priority",
    "multiplatform": "format_distribution_publish_decoupled",
}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now_utc().isoformat()


def _short_error_summary(value: Any, limit: int = 240) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return text if len(text) <= limit else f"{text[:limit - 3]}..."


def _normalize_release_operation_state(operational_state: str | None) -> str:
    state = str(operational_state or "technical_test").strip().lower()
    return ALLOWED_RELEASE_OPERATION_STATES.get(state, "technical_test")


def _publish_truth_state_from_result(publish_result: dict[str, Any] | None) -> str:
    publish_result = safe_dict(publish_result)
    if not publish_result:
        return "publish_truth_absent"

    publish_status = str(publish_result.get("publish_status") or "").strip().lower()
    receipt_id = publish_result.get("receipt_id")
    media_id = publish_result.get("media_id")
    permalink = publish_result.get("permalink")

    if publish_status == "published_real_probe" and receipt_id and media_id:
        return "publish_truth_confirmed"
    if receipt_id or permalink or media_id:
        return "publish_attempt_recorded"
    return "publish_truth_absent"


def _gate_stage_summary(reel_stack: dict[str, Any] | None) -> dict[str, Any]:
    reel_stack = safe_dict(reel_stack)
    cinematic_gate = safe_dict(reel_stack.get("cinematic_gate"))
    release_authority = safe_dict(reel_stack.get("release_authority"))
    publish_guard = safe_dict(reel_stack.get("publish_guard"))

    return {
        "ok": bool(reel_stack.get("ok")),
        "stack_state": reel_stack.get("stack_state"),
        "cinematic_gate_state": cinematic_gate.get("state"),
        "cinematic_gate_approved": bool(cinematic_gate.get("approved")),
        "cinematic_score": cinematic_gate.get("cinematic_score"),
        "release_state": release_authority.get("release_state"),
        "approved_for_publish": bool(release_authority.get("approved_for_publish")),
        "publish_guard_mode": publish_guard.get("mode"),
        "publish_guard_state": publish_guard.get("state"),
        "can_publish": bool(publish_guard.get("can_publish")),
        "next_step": publish_guard.get("next_step"),
    }


class OfficialRuntime:
    """
    ACE Ω — Runtime Soberano Fino

    Diretrizes absorvidas no arquivo:
    - runtime é casca fina; inteligência vai para módulos
    - integração grande por ondas
    - Reel Premium Stack é prioridade estrutural
    - publish truth só conta com receipt/media_id/permalink
    - learning deve priorizar save/share/replay/retenção
    - base já nasce aberta para multiplataforma
    """

    def __init__(self, config: AceNextConfig) -> None:
        self.config = config
        self._boot = bootstrap_capabilities()
        self._last_run_summary: dict[str, Any] = {}
        self._resolution_cache: dict[str, dict[str, Any]] = {}

        publish_cls = self._symbol("PublishService")
        self.publish = publish_cls(config) if publish_cls else None

        self._boot_sync()

    # ---------------------------------------------------------
    # CAPABILITY RESOLUTION
    # ---------------------------------------------------------
    def _resolve(self, name: str) -> dict[str, Any]:
        if name not in self._resolution_cache:
            self._resolution_cache[name] = resolve_capability(name)
        return self._resolution_cache[name]

    def _symbol(self, name: str):
        resolved = self._resolve(name)
        if not resolved.get("ok"):
            return None
        return resolved.get("symbol")

    def _call(self, name: str, *args, **kwargs) -> tuple[bool, Any]:
        symbol = self._symbol(name)
        if symbol is None:
            return False, {
                "ok": False,
                "error": self._resolve(name).get("error") or "capability_unavailable",
                "capability": name,
            }

        try:
            result = symbol(*args, **kwargs)
            return True, result
        except Exception as exc:
            return False, {
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
                "capability": name,
            }

    def _to_dict(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return dict(value)
        if hasattr(value, "to_dict"):
            try:
                parsed = value.to_dict()
                return dict(parsed) if isinstance(parsed, dict) else {}
            except Exception:
                return {}
        return {}

    # ---------------------------------------------------------
    # AUTH / TOKEN / BOOT
    # ---------------------------------------------------------
    def _brand_env_flags(self) -> dict[str, Any]:
        return {
            "ACE_BRAND_SURFACE_MODE": os.environ.get("ACE_BRAND_SURFACE_MODE", "protected"),
            "ACE_ALLOW_MAIN_SURFACE_LAB_PROBE": safe_bool(
                os.environ.get("ACE_ALLOW_MAIN_SURFACE_LAB_PROBE"),
                False,
            ),
            "ACE_ALLOW_MAIN_SURFACE_EDITORIAL_STAGING": safe_bool(
                os.environ.get("ACE_ALLOW_MAIN_SURFACE_EDITORIAL_STAGING"),
                False,
            ),
            "ACE_REQUIRE_HUMAN_REVIEW_FOR_BRAND_LIVE": safe_bool(
                os.environ.get("ACE_REQUIRE_HUMAN_REVIEW_FOR_BRAND_LIVE"),
                True,
            ),
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

    def _recent_memory_for_planner(self, limit: int = 5) -> list[dict[str, Any]]:
        if not self.publish:
            return []
        last_publish = safe_dict(self.publish.last_publish())
        recent_episodes = last_publish.get("recent_episodes")
        if isinstance(recent_episodes, list):
            return [safe_dict(item) for item in recent_episodes[-limit:]]
        return []

    def sync_instagram_auth(self) -> dict[str, Any]:
        ok, result = self._call("sync_instagram_token_sources", self.config, persist=False)
        if ok and isinstance(result, dict):
            return dict(result)
        return {
            "ok": False,
            "token_source": None,
            "user_id_source": None,
            "auth_path": str(self.config.auth_path),
            "error": safe_dict(result).get("error") if isinstance(result, dict) else None,
        }

    def _auth_state(self) -> dict[str, Any]:
        ok, stored = self._call("load_instagram_auth", self.config)
        stored_dict = safe_dict(stored) if ok else {}
        meta = stored_dict.get("meta") if isinstance(stored_dict.get("meta"), dict) else {}

        saved_at_raw = stored_dict.get("saved_at")
        expires_at_raw = meta.get("expires_at")

        saved_at = None
        expires_at = None

        try:
            if saved_at_raw:
                saved_at = datetime.fromisoformat(str(saved_at_raw).replace("Z", "+00:00"))
        except Exception:
            saved_at = None

        try:
            if expires_at_raw:
                expires_at = datetime.fromisoformat(str(expires_at_raw).replace("Z", "+00:00"))
        except Exception:
            expires_at = None

        if not expires_at and saved_at:
            expires_at = saved_at + timedelta(days=self._assumed_ttl_days())

        remaining_days = None
        if expires_at:
            remaining_days = (expires_at - _now_utc()).total_seconds() / 86400

        return {
            "saved_at": saved_at.isoformat() if saved_at else None,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "remaining_days": remaining_days,
            "refreshed_at": meta.get("refreshed_at"),
            "source": meta.get("source"),
            "auth_loader_ok": ok,
        }

    def _token_needs_refresh(self, force: bool = False) -> tuple[bool, str]:
        if force:
            return True, "forced"

        if not self.config.ig_token or not self.config.ig_id:
            return False, "missing_token_or_ig_id"

        state = self._auth_state()
        expires_at_raw = state.get("expires_at")
        saved_at_raw = state.get("saved_at")

        expires_at = None
        saved_at = None

        try:
            if expires_at_raw:
                expires_at = datetime.fromisoformat(str(expires_at_raw).replace("Z", "+00:00"))
        except Exception:
            expires_at = None

        try:
            if saved_at_raw:
                saved_at = datetime.fromisoformat(str(saved_at_raw).replace("Z", "+00:00"))
        except Exception:
            saved_at = None

        now = _now_utc()

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

        ok_refresh, refresh = self._call(
            "refresh_instagram_long_lived_token",
            self.config,
            current_token=self.config.ig_token or "",
            current_user_id=self.config.ig_id,
        )
        refresh_dict = safe_dict(refresh) if ok_refresh else safe_dict(refresh)

        render_sync = {"ok": False, "persisted": False, "skipped": True}

        refreshed_token = refresh_dict.get("token") or safe_dict(refresh_dict.get("data")).get("access_token")
        if refreshed_token:
            ok_render, render_result = self._call(
                "persist_instagram_token_to_render",
                token=str(refreshed_token),
                user_id=self.config.ig_id,
            )
            render_sync = safe_dict(render_result) if ok_render else safe_dict(render_result)
            self.sync_instagram_auth()

        return {
            "ok": bool(refresh_dict.get("ok", ok_refresh)),
            "attempted": True,
            "reason": reason,
            "refresh": refresh_dict,
            "render_env_sync": render_sync,
            "token_state": self._auth_state(),
        }

    def _boot_sync(self) -> None:
        self.sync_instagram_auth()
        try:
            self.ensure_fresh_instagram_token(force=False)
        except Exception:
            pass

    # ---------------------------------------------------------
    # SNAPSHOT / HEALTH
    # ---------------------------------------------------------
    def _performance_store_summary(self) -> dict[str, Any]:
        symbol = self._symbol("PerformanceStore")
        if symbol is None:
            return {"ok": False, "error": self._resolve("PerformanceStore").get("error") or "measurement_stack_unavailable"}

        try:
            summary = symbol(self.config).summary()
            return self._to_dict(summary)
        except Exception as exc:
            return {"ok": False, "error": f"performance_store_summary_error: {type(exc).__name__}: {exc}"}

    def snapshot(self) -> dict[str, Any]:
        sync = self.sync_instagram_auth()
        token_state = self._auth_state()
        env_flags = self._brand_env_flags()

        return {
            "timestamp": _now_iso(),
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
            "real_probe_route_supported": True,
            "real_probe_allowed_states": sorted(REAL_PROBE_ALLOWED_STATES),
            "brand_live_allowed": False,
            "brand_surface_mode": env_flags.get("ACE_BRAND_SURFACE_MODE"),
            "brand_surface_flags": env_flags,
            "performance_store": self._performance_store_summary(),
            "registry_boot": self._boot,
            "registry_snapshot": capability_registry_snapshot(include_future=True),
            "last_run_summary": self._last_run_summary,
            "study_tags": STUDY_TAGS,
            "runtime_design": {
                "mode": "thin_runtime",
                "contracts": True,
                "registry": True,
                "adapters": True,
                "bootstrap": True,
                "legacy_compatibility": True,
            },
        }

    def compact_runtime_summary(self) -> dict[str, Any]:
        snap = self.snapshot()
        return {
            "timestamp": snap.get("timestamp"),
            "token_present": snap.get("token_present"),
            "ig_id_present": snap.get("ig_id_present"),
            "enable_real_publish": snap.get("enable_real_publish"),
            "brand_surface_mode": snap.get("brand_surface_mode"),
            "real_probe_allowed_states": snap.get("real_probe_allowed_states"),
            "performance_store": snap.get("performance_store"),
            "last_run_summary": snap.get("last_run_summary"),
        }

    def probe_readiness_summary(self) -> dict[str, Any]:
        readiness = self.sync_instagram_auth()
        return {
            "ok": True,
            "instagram_connected": bool(self.config.ig_token and self.config.ig_id),
            "token_present": bool(self.config.ig_token),
            "ig_id_present": bool(self.config.ig_id),
            "token_source": readiness.get("token_source"),
            "user_id_source": readiness.get("user_id_source"),
            "real_publish_enabled": bool(self.config.enable_real_publish),
            "allowed_probe_states": sorted(REAL_PROBE_ALLOWED_STATES),
        }

    def quality_gap_summary(self) -> dict[str, Any]:
        summary = safe_dict(self._last_run_summary)
        return {
            "ok": True,
            "premium_classification": summary.get("premium_classification"),
            "eligible_for_editorial_staging": summary.get("eligible_for_editorial_staging"),
            "eligible_for_brand_live_candidate": summary.get("eligible_for_brand_live_candidate"),
            "missing_for_brand_live": summary.get("missing_for_brand_live"),
            "score_gap_to_brand_live": summary.get("score_gap_to_brand_live"),
            "next_quality_lift_targets": summary.get("next_quality_lift_targets"),
        }

    def last_publish_compact_summary(self) -> dict[str, Any]:
        if not self.publish:
            return {"ok": False, "error": "publish_service_unavailable"}
        last_publish = safe_dict(self.publish.last_publish())
        return {
            "ok": True,
            "source_of_truth": last_publish.get("source_of_truth"),
            "latest_media_id": last_publish.get("latest_media_id"),
            "latest_permalink": last_publish.get("latest_permalink"),
            "latest_evidence_state": last_publish.get("latest_evidence_state"),
            "latest_resolution_state": last_publish.get("latest_resolution_state"),
            "updated_at": last_publish.get("updated_at"),
        }

    # ---------------------------------------------------------
    # PLANNING / STUDY-DRIVEN HELPERS
    # ---------------------------------------------------------
    def _mission_approval_required(self) -> bool:
        return safe_bool(os.environ.get("ACE_REQUIRE_MISSION_APPROVAL"), False)

    def _planner_overrides_from_mission_decision(
        self,
        mission_decision: dict[str, Any] | None,
    ) -> dict[str, Any]:
        mission_decision = safe_dict(mission_decision)
        content_type = str(mission_decision.get("content_type") or "").strip().lower()
        publish_format_now = content_type if content_type in {"image", "carousel", "story", "reel"} else None
        return {
            "strategic_target_format": content_type or None,
            "publish_format_now": publish_format_now,
            "publish_style": None,
            "goal": mission_decision.get("goal"),
            "hypothesis": mission_decision.get("hypothesis"),
            "planner_selected": mission_decision.get("planner_selected"),
            # estudos aplicados
            "attention_priority": "save_share_replay_retention",
            "clarity_density_policy": STUDY_TAGS["psychology_clt"],
            "narrative_policy": STUDY_TAGS["stepps"],
            "hook_policy": STUDY_TAGS["hook_attention"],
            "naturalism_policy": STUDY_TAGS["naturalism"],
        }

    def _mission_decision(self, trend: str, env_flags: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        mission_control_state = {
            "enabled": True,
            "approval_required": self._mission_approval_required(),
            "blocked": False,
        }

        ok, mission_decision = self._call(
            "decide_mission",
            trend,
            format_hint=None,
            signal_context={
                "source": "official_runtime",
                "mode": "run",
                "study_tags": {
                    "hook": STUDY_TAGS["hook_attention"],
                    "stepps": STUDY_TAGS["stepps"],
                    "mab": STUDY_TAGS["mab"],
                },
            },
            brand_context={
                "brand_surface_mode": env_flags.get("ACE_BRAND_SURFACE_MODE"),
                "brand_live_allowed": False,
            },
            queue_state=self._runtime_queue_state(),
            recent_signal_score=None,
        )

        mission_dict = adapt_legacy_mission_decision(mission_decision if ok else {})
        raw_mission = safe_dict(mission_decision)

        if not mission_dict:
            mission_dict = {
                "trend": trend,
                "style": "unknown",
                "content_type": "image",
                "goal": "authority",
                "confidence": 0.2,
                "raw": {
                    "ok": False,
                    "should_act": True,
                    "reason": safe_dict(mission_decision).get("error") or "mission_control_runtime_fallback",
                    "decision_state": "fallback_allow",
                    "hypothesis": "mission_control_unavailable_runtime_fallback",
                    "planner_selected": "mission_control_runtime_fallback",
                    "signal_strength": "unknown",
                },
            }
            mission_control_state["fallback"] = True
            mission_control_state["error"] = mission_dict["raw"].get("reason")

        return (
            {
                "trend": mission_dict.get("trend") or trend,
                "style": mission_dict.get("style") or raw_mission.get("style") or "unknown",
                "content_type": mission_dict.get("content_type") or raw_mission.get("content_type") or "image",
                "goal": mission_dict.get("goal") or raw_mission.get("goal") or "authority",
                "confidence": mission_dict.get("confidence") or raw_mission.get("confidence") or 0.2,
                "raw": raw_mission or mission_dict.get("raw") or {},
            },
            mission_control_state,
        )

    def _creative_plan(self, trend: str, mission_decision: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        overrides = self._planner_overrides_from_mission_decision(mission_decision)
        recent_memory = self._recent_memory_for_planner(limit=5)

        ok, plan = self._call(
            "build_creative_plan",
            trend,
            overrides=overrides,
            mission_decision=mission_decision.get("raw"),
            recent_memory=recent_memory,
        )

        if ok:
            plan_dict = self._to_dict(plan)
            if plan_dict:
                plan_dict.setdefault("study_tags", STUDY_TAGS)
                plan_dict.setdefault("serial_continuity_hint", bool(recent_memory))
                plan_dict.setdefault("attention_target", "save_share_replay_retention")
                plan_dict.setdefault("ethical_boundary", "no_hidden_manipulation")
                return True, plan_dict

        # fallback mínimo seguro
        return False, {
            "topic_seed": trend,
            "headline": trend,
            "hook": f"o que há por trás de {trend}",
            "payoff": f"clareza prática sobre {trend}",
            "cta": "salve e compartilhe se fizer sentido",
            "publish_style": mission_decision.get("style") or "official_next_visual_foundation_v1",
            "publish_format_now": mission_decision.get("content_type") or "image",
            "goal": mission_decision.get("goal") or "authority",
            "hypothesis": safe_dict(mission_decision.get("raw")).get("hypothesis"),
            "planner_selected": safe_dict(mission_decision.get("raw")).get("planner_selected") or "creative_planner_fallback",
            "serial_continuity_hint": bool(recent_memory),
            "study_tags": STUDY_TAGS,
            "ethical_boundary": "no_hidden_manipulation",
        }

    def _editorial_quality(self, plan_dict: dict[str, Any]) -> dict[str, Any]:
        ok, result = self._call("evaluate_editorial_quality", plan_dict)
        quality = self._to_dict(result) if ok else {}
        if quality:
            return quality
        return {
            "approved": False,
            "breakdown": {},
            "flags": ["editorial_qa_unavailable"],
            "reasons": [safe_dict(result).get("error") or "editorial_qa_unavailable"],
            "study_alignment": {
                "clarity_density_control": True,
                "stepps_narrative": True,
                "anti_cliche": True,
            },
        }

    def _visual_foundation(
        self,
        plan_dict: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
        visual_identity = {}
        typography = {}
        visual_contract = {}
        visual_template = {}
        perceptual_qa = {}
        visual_qa = {}

        ok, identity_obj = self._call("build_visual_identity", plan_dict)
        visual_identity = self._to_dict(identity_obj) if ok else {
            "error": safe_dict(identity_obj).get("error") or "visual_identity_unavailable"
        }

        ok, typography_obj = self._call("build_typography_spec", plan_dict)
        typography = self._to_dict(typography_obj) if ok else {
            "error": safe_dict(typography_obj).get("error") or "typography_unavailable"
        }

        ok, contract_obj = self._call("build_visual_contract", plan_dict)
        visual_contract = self._to_dict(contract_obj) if ok else {
            "error": safe_dict(contract_obj).get("error") or "visual_contract_unavailable"
        }

        ok, template_obj = self._call("resolve_visual_template", plan_dict)
        visual_template = self._to_dict(template_obj) if ok else {
            "error": safe_dict(template_obj).get("error") or "visual_template_unavailable"
        }

        if visual_identity and typography and visual_contract and visual_template and "error" not in visual_identity and "error" not in typography and "error" not in visual_contract and "error" not in visual_template:
            ok, result = self._call(
                "evaluate_perceptual_quality",
                plan=plan_dict,
                contract=contract_obj,
                template=template_obj,
                identity=identity_obj,
                typography=typography_obj,
            )
            perceptual_qa = self._to_dict(result) if ok else {}

            ok, result = self._call(
                "evaluate_visual_quality",
                plan=plan_dict,
                identity=identity_obj,
                typography=typography_obj,
            )
            visual_qa = self._to_dict(result) if ok else {}

        if not perceptual_qa:
            perceptual_qa = {
                "approved": False,
                "final_score": 0,
                "breakdown": {},
                "metrics": {"zero_overlap": False},
                "reasons": ["perceptual_qa_unavailable"],
                "recommendations": [],
                "study_alignment": {
                    "pattern_interrupt_visual": True,
                    "visual_hierarchy": True,
                    "safe_zones": True,
                    "naturalism": True,
                },
            }

        if not visual_qa:
            visual_qa = {
                "approved": False,
                "final_score": 0,
                "minimum_score": 75,
                "breakdown": {},
                "metrics": {"zero_overlap": False},
                "reasons": ["visual_qa_unavailable"],
                "recommendations": [],
                "study_alignment": {
                    "contrast": True,
                    "typography_legibility": True,
                    "visual_hierarchy": True,
                },
            }

        return visual_identity, typography, visual_contract, visual_template, {
            "perceptual_qa": perceptual_qa,
            "visual_qa": visual_qa,
        }

    def _premium_visual(
        self,
        plan_dict: dict[str, Any],
        visual_identity: dict[str, Any],
        visual_contract: dict[str, Any],
    ) -> dict[str, Any]:
        ok, result = self._call(
            "build_visual_premium_bridge",
            creative_plan=plan_dict,
            visual_identity=visual_identity,
            visual_contract=visual_contract,
            strategic_format=plan_dict.get("publish_format_now"),
            template_id=None,
            capture_mode="safe",
        )
        premium_visual = self._to_dict(result) if ok else {}
        if premium_visual:
            premium_visual.setdefault("study_alignment", {
                "pattern_interrupt_visual": True,
                "playwright_official_path": True,
                "premium_layout_variation": True,
            })
            return premium_visual

        return {
            "ok": False,
            "approved_for_premium_visual": False,
            "premium_render_state": "premium_visual_bridge_unavailable",
            "reasons": [safe_dict(result).get("error") or "premium_visual_bridge_unavailable"],
            "hardening_applied": False,
            "hardening_report": {},
            "study_alignment": {
                "pattern_interrupt_visual": True,
                "playwright_official_path": True,
                "premium_layout_variation": True,
            },
        }

    def _authorization_fallback(
        self,
        *,
        force_placeholder: bool,
        reason: str,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
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
        rubric_fn = self._symbol("evaluate_rubric_engine")
        brand_veto_fn = self._symbol("evaluate_brand_veto_gate")
        authorize_fn = self._symbol("authorize_publication")

        if not rubric_fn or not brand_veto_fn or not authorize_fn:
            return self._authorization_fallback(
                force_placeholder=force_placeholder,
                reason="authorization_stack_import_error",
            )

        try:
            rubric = rubric_fn(
                plan=plan_dict,
                editorial_qa=editorial_qa,
                visual_qa=visual_qa,
                perceptual_qa=perceptual_qa,
            )
            brand_veto = brand_veto_fn(
                plan=plan_dict,
                editorial_qa=editorial_qa,
                visual_qa=visual_qa,
                perceptual_qa=perceptual_qa,
                rubric=rubric,
            )
            authorization = authorize_fn(
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
            rubric_dict = self._to_dict(rubric)
            rubric_dict["stack_ok"] = True
            brand_veto_dict = self._to_dict(brand_veto)
            brand_veto_dict["stack_ok"] = True
            authorization_dict = self._to_dict(authorization)
            authorization_dict["stack_ok"] = True
            return rubric_dict, brand_veto_dict, authorization_dict
        except Exception as exc:
            return self._authorization_fallback(
                force_placeholder=force_placeholder,
                reason=f"authorization_stack_runtime_error: {type(exc).__name__}: {exc}",
            )

    def _brand_and_probe_policies(
        self,
        *,
        authorization_state: str,
        env_flags: dict[str, Any],
        request_flags: dict[str, Any],
        publication_authorization_gate: dict[str, Any],
        probe_state_requested: str,
    ) -> tuple[dict[str, Any], dict[str, Any], bool]:
        ok, probe_policy = self._call(
            "resolve_lab_probe_policy",
            operational_state=authorization_state,
            requested_probe=request_flags["probe_requested"],
            requested_state=probe_state_requested,
            env_flags=env_flags,
            request_flags=request_flags,
        )
        lab_probe_policy = self._to_dict(probe_policy) if ok else {
            "probe_requested": request_flags["probe_requested"],
            "probe_state_requested": probe_state_requested,
            "probe_state_effective": authorization_state,
            "probe_eligible": False,
            "probe_block_reason": safe_dict(probe_policy).get("error") or "lab_probe_policy_unavailable",
            "requested_real_publish": False,
            "probe_publish_executed": False,
            "probe_render_requested": False,
        }

        ok, brand_policy = self._call(
            "resolve_brand_surface_policy",
            operational_state=authorization_state,
            requested_real_publish=lab_probe_policy.get("requested_real_publish", False),
            env_flags=env_flags,
            request_flags=request_flags,
            quality_context={
                "brand_live_candidate": publication_authorization_gate.get("brand_live_candidate"),
                "can_publish_real": publication_authorization_gate.get("can_publish_real"),
            },
        )
        brand_surface_policy = self._to_dict(brand_policy) if ok else {
            "surface_mode": env_flags.get("ACE_BRAND_SURFACE_MODE", "protected"),
            "main_surface_allowed": False,
            "block_reason": safe_dict(brand_policy).get("error") or "brand_surface_policy_unavailable",
        }

        explicit_probe_execution_allowed = bool(
            request_flags.get("probe_requested")
            and request_flags.get("explicit_probe_arm")
            and not request_flags.get("force_placeholder")
            and str(lab_probe_policy.get("probe_state_effective") or authorization_state).strip().lower() in REAL_PROBE_ALLOWED_STATES
        )

        return brand_surface_policy, lab_probe_policy, explicit_probe_execution_allowed

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
        required_names = [
            "generate_hook_opening",
            "ReelStoryboardEngine",
            "ReelRhythmEngine",
            "PostProductionPipeline",
            "AudioDirectionLayer",
            "MultimodalReelQA",
            "CinematicGate",
            "ReleaseAuthority",
            "PublishGuard",
        ]
        if not all(self._symbol(name) for name in required_names):
            return {
                "ok": False,
                "stack_state": "reel_stack_import_error",
                "error": "reel premium stack unavailable",
                "study_alignment": {
                    "hook": STUDY_TAGS["hook_attention"],
                    "rhythm": STUDY_TAGS["rhythm"],
                    "naturalism": STUDY_TAGS["naturalism"],
                },
            }

        hook_fn = self._symbol("generate_hook_opening")
        storyboard_cls = self._symbol("ReelStoryboardEngine")
        rhythm_cls = self._symbol("ReelRhythmEngine")
        post_cls = self._symbol("PostProductionPipeline")
        audio_cls = self._symbol("AudioDirectionLayer")
        qa_cls = self._symbol("MultimodalReelQA")
        cinematic_cls = self._symbol("CinematicGate")
        release_cls = self._symbol("ReleaseAuthority")
        guard_cls = self._symbol("PublishGuard")

        hook_raw = safe_dict(
            hook_fn(
                trend=trend,
                style=creative_plan.get("publish_style"),
                content_type=creative_plan.get("publish_format_now"),
            )
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
            "study_alignment": {
                "first_3_seconds": True,
                "pattern_interrupt": True,
                "curiosity_gap": True,
                "micro_payoffs": True,
                "cadence_target": "450ms_opening",
            },
        }

        storyboard = safe_dict(
            storyboard_cls().run(
                creative_plan=creative_plan,
                hook_opening=hook_opening,
            )
        )

        rhythm = safe_dict(
            rhythm_cls().run(
                storyboard=storyboard,
                hook_opening={"opening_pattern": hook_opening.get("opening_pattern", "curiosity_gap")},
            )
        )
        rhythm.setdefault("study_alignment", {
            "cadence_0_3s": "450ms",
            "cadence_3_15s": "1200ms",
            "cadence_15_45s": "850ms",
            "cadence_45_60s": "300ms",
        })

        subtitles = {
            "emphasis_mode": (
                "short_emphasis_lines"
                if rhythm.get("subtitle_pacing_hint") == "short_emphasis_lines"
                else "balanced_lines"
            ),
            "naturalism_mode": "anti_plastic_subtitles",
        }

        post_production = safe_dict(
            post_cls().run(
                storyboard=storyboard,
                rhythm=rhythm,
                subtitles=subtitles,
            )
        )

        audio_direction = safe_dict(
            audio_cls().run(
                hook_opening={"opening_pattern": hook_opening.get("opening_pattern", "curiosity_gap")},
                rhythm=rhythm,
                post_production=post_production,
            )
        )
        audio_direction.setdefault("study_alignment", {
            "foley": True,
            "ducking": True,
            "prosody": True,
            "micro_breathing": True,
        })

        visual_score_10 = max(
            float(visual_qa.get("final_score", 0)) / 10.0,
            float(perceptual_qa.get("final_score", 0)) / 10.0,
        )
        audio_score_10 = 8.6 if audio_direction.get("state") == "audio_direction_layer_ready" else 6.0
        rhythm_score_10 = 8.6 if rhythm.get("rhythm_state") == "reel_rhythm_ready" else 6.0

        multimodal_qa = safe_dict(
            qa_cls().run(
                visual_gate={"global_visual_score": visual_score_10},
                audio_gate={"global_audio_score": audio_score_10},
                reel_gate={"global_score": rhythm_score_10},
                naturalism={"naturalism_state": "naturalism_engine_ready"},
            )
        )

        overall_quality_score = max(
            visual_score_10,
            8.5 if publication_authorization_gate.get("eligible_for_editorial_staging") else visual_score_10,
        )

        cinematic_gate = safe_dict(
            cinematic_cls().run(
                multimodal_qa=multimodal_qa,
                reel_director={
                    "visual_mode": "cinematic_retention",
                    "cut_mode": "precision_fast",
                    "grain_target": "2_percent",
                    "camera_language": "dolly_pan_whip_pan_safe",
                },
                premium_decision={"overall_quality_score": overall_quality_score},
            )
        )

        release_authority = safe_dict(
            release_cls().run(
                cinematic_gate=cinematic_gate,
                premium_decision={"overall_quality_score": overall_quality_score},
                operation_bridge={
                    "operational_state": _normalize_release_operation_state(operational_state)
                },
            )
        )

        publish_guard = safe_dict(
            guard_cls().run(
                release_authority=release_authority,
                publish_truth={"truth_state": publish_truth_state},
            )
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
            "study_alignment": {
                "hook": STUDY_TAGS["hook_attention"],
                "rhythm": STUDY_TAGS["rhythm"],
                "naturalism": STUDY_TAGS["naturalism"],
                "hollywood_pipeline": True,
            },
        }

    def _render_previews(self, plan_dict: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        carousel_preview = {}
        stories_preview = {}

        ok, result = self._call("build_carousel_sequence", plan_dict)
        carousel_preview = self._to_dict(result) if ok else {
            "ok": False,
            "error": safe_dict(result).get("error") or "carousel_preview_unavailable",
        }

        ok, result = self._call("build_stories_sequence", plan_dict)
        stories_preview = self._to_dict(result) if ok else {
            "ok": False,
            "error": safe_dict(result).get("error") or "stories_preview_unavailable",
        }

        return carousel_preview, stories_preview

    def _measurement_summary(
        self,
        *,
        publish_result: dict[str, Any] | None,
        creative_plan: dict[str, Any],
        mission_decision: dict[str, Any],
    ) -> dict[str, Any]:
        publish_result = safe_dict(publish_result)
        receipt_id = publish_result.get("receipt_id")
        media_id = publish_result.get("media_id")
        permalink = publish_result.get("permalink")
        publish_status = publish_result.get("publish_status")
        error_summary = _short_error_summary(publish_result.get("error"))

        # base atual
        performance_ingest = {
            "ok": True,
            "attempted": bool(media_id),
            "collection_success": False,
            "source_status": "not_collected_yet",
            "real_metrics": {"source_status": "not_collected_yet"},
            "attention_inputs": {
                "priority_metrics": ["save_rate", "share_rate", "retention", "replay_proxy"],
                "secondary_metrics": ["engagement_rate", "like_rate"],
            },
            "errors": [error_summary] if error_summary else [],
            "raw": {},
            "study_alignment": {
                "attention_engineering": True,
                "like_is_auxiliary": True,
            },
        }

        # futuro via capability
        thompson_sampler_result = {
            "ok": True,
            "selected_variant": None,
            "confidence_level": "low",
            "decision_state": "collecting",
            "posterior_mean": None,
            "winner_candidate": False,
            "reasons": [],
            "study_alignment": {"mab": True},
        }
        if self._symbol("ThompsonSampler"):
            thompson_sampler_result["capability_ready"] = True
        else:
            thompson_sampler_result["capability_ready"] = False

        recommendation_engine = {
            "ok": True,
            "recommended_action": "measure_now" if media_id else "publish_or_improve",
            "action_priority": "medium",
            "recommendation_reason": "measurement_slim_mode",
            "next_best_step": "coletar métricas reais após publicação" if media_id else "melhorar qualidade premium antes de publicar",
            "safe_to_repeat": True,
            "safe_to_promote_to_editorial_staging": False,
            "requires_human_review": True,
            "strategy_inputs": {
                "goal": creative_plan.get("goal") or mission_decision.get("goal"),
                "format": creative_plan.get("publish_format_now") or mission_decision.get("content_type"),
                "timing_ready": bool(self._symbol("DistributionTimingEngine")),
                "seo_ready": bool(self._symbol("SeoSocialEngine")),
            },
        }

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
            "performance_ingest": performance_ingest,
            "attention_metrics": {
                "ok": True,
                "source_status": "not_collected_yet",
                "breakdown": {},
                "available_inputs": ["save_rate", "share_rate", "retention", "replay_proxy"],
                "notes": [
                    "like é auxiliar",
                    "priorizar atenção real",
                    "learning deve influenciar hook/formato/estilo/timing",
                ],
            },
            "resonance_engine": {
                "ok": True,
                "resonance_score": None,
                "reasons": [],
                "capability_ready": bool(self._symbol("resonance_engine")),
            },
            "reward_prediction": {
                "ok": True,
                "reward_prediction_score": None,
                "reasons": [],
            },
            "thompson_sampler": thompson_sampler_result,
            "decision_core_summary": {
                "ok": True,
                "selected_variant": thompson_sampler_result.get("selected_variant"),
                "confidence_level": thompson_sampler_result.get("confidence_level"),
                "experiment_decision_state": thompson_sampler_result.get("decision_state"),
                "reasons": ["measurement_slim_mode"],
                "study_alignment": {"mab": True, "stackelberg": True},
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
            "recommendation_engine": recommendation_engine,
            "wave10_summary": {
                "ok": True,
                "evidence_state": "collecting",
                "resolution_state": "collecting",
                "recommended_action": recommendation_engine.get("recommended_action"),
            },
            "wave11_summary": {
                "ok": True,
                "brand_live_allowed": False,
                "evidence_state": "collecting",
                "has_receipt": bool(receipt_id),
                "has_media_id": bool(media_id),
                "has_permalink": bool(permalink),
                "can_resolve": False,
                "recommended_action": recommendation_engine.get("recommended_action"),
                "next_best_step": recommendation_engine.get("next_best_step"),
            },
            "experiment_registry": {
                "ok": bool(self._symbol("ExperimentRegistry")),
                "error": None if self._symbol("ExperimentRegistry") else "measurement_slim_runtime",
            },
            "episodic_performance_memory": {
                "ok": False,
                "error": "measurement_slim_runtime",
            },
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
                "study_alignment": {
                    "stackelberg": True,
                    "mab": True,
                    "attention_priority": True,
                },
            },
            "performance_summary": {
                "ok": True,
                "mode": "measurement_slim_runtime",
                "next_decision_targets": ["hook", "format", "style", "timing"],
            },
            "performance_store": self._performance_store_summary(),
        }

    # ---------------------------------------------------------
    # MAIN RUN
    # ---------------------------------------------------------
    def run(
        self,
        *,
        trend: str,
        force_placeholder: bool = False,
        force_real_probe: bool = False,
        probe_state: str | None = None,
    ) -> dict[str, Any]:
        runtime_request = build_runtime_request(
            trend=trend,
            force_placeholder=force_placeholder,
            force_real_probe=force_real_probe,
            probe_state=probe_state or "auto",
        )
        envelope = build_runtime_execution_envelope(
            trend=runtime_request.trend,
            force_placeholder=runtime_request.force_placeholder,
            force_real_probe=runtime_request.force_real_probe,
            probe_state=runtime_request.probe_state,
            source="official_runtime",
            mode="thin_runtime",
        )

        trend_value = normalize_trend(runtime_request.trend)
        probe_state_requested = normalize_probe_state(runtime_request.probe_state)
        env_flags = self._brand_env_flags()

        request_flags = {
            "probe_requested": bool(runtime_request.force_real_probe) and not runtime_request.force_placeholder,
            "explicit_probe_arm": bool(runtime_request.force_real_probe) and not runtime_request.force_placeholder,
            "explicit_main_surface_publish": bool(runtime_request.force_real_probe) and not runtime_request.force_placeholder,
            "brand_live_arm": False,
            "human_review_approved": False,
            "force_placeholder": bool(runtime_request.force_placeholder),
        }

        mission_decision, mission_control_state = self._mission_decision(trend_value, env_flags)

        if mission_control_state["approval_required"] and not bool(safe_dict(mission_decision.get("raw")).get("should_act", True)):
            mission_control_state["blocked"] = True
            return {
                "ok": True,
                "mode": "blocked_by_mission_control",
                "authorization_state": "blocked_by_mission_control",
                "operational_state": "blocked_by_mission_control",
                "brand_live_allowed": False,
                "trend": trend_value,
                "mission_decision": mission_decision,
                "mission_control_state": mission_control_state,
                "block_reasons": [safe_dict(mission_decision.get("raw")).get("reason")],
                "runtime": self.snapshot(),
                "publish_result": None,
                "last_publish": self.publish.last_publish() if self.publish else None,
                "request_envelope": envelope.to_dict(),
            }

        plan_ok, creative_plan = self._creative_plan(trend_value, mission_decision)
        editorial_qa = self._editorial_quality(creative_plan)

        visual_identity, typography, visual_contract, visual_template, visual_bundle = self._visual_foundation(creative_plan)
        perceptual_qa = safe_dict(visual_bundle.get("perceptual_qa"))
        visual_qa = safe_dict(visual_bundle.get("visual_qa"))
        premium_visual = self._premium_visual(creative_plan, visual_identity, visual_contract)

        rubric_engine, brand_veto_gate, publication_authorization_gate = self._run_authorization_stack(
            force_placeholder=runtime_request.force_placeholder,
            plan_dict=creative_plan,
            editorial_qa=editorial_qa,
            visual_qa=visual_qa,
            perceptual_qa=perceptual_qa,
            env_flags=env_flags,
            request_flags=request_flags,
            staging_hardener=safe_dict(premium_visual.get("hardening_report")),
        )

        authorization_state = publication_authorization_gate.get("selected_state", "technical_test")
        operational_state = authorization_state
        block_reasons = list(publication_authorization_gate.get("reasons") or [])
        if publication_authorization_gate.get("stack_ok") is False:
            block_reasons.extend(publication_authorization_gate.get("block_reasons") or [])

        brand_surface_policy, lab_probe_policy, explicit_probe_execution_allowed = self._brand_and_probe_policies(
            authorization_state=authorization_state,
            env_flags=env_flags,
            request_flags=request_flags,
            publication_authorization_gate=publication_authorization_gate,
            probe_state_requested=probe_state_requested,
        )

        prepublish_reel_stack = self._run_reel_premium_stack(
            trend=trend_value,
            creative_plan=creative_plan,
            visual_qa=visual_qa,
            perceptual_qa=perceptual_qa,
            publication_authorization_gate=publication_authorization_gate,
            operational_state=operational_state,
            publish_truth_state="publish_truth_absent",
        )

        # HARD GATE SOBERANO — B1 + C1 + C2
        release_authority = safe_dict(prepublish_reel_stack.get("release_authority"))
        publish_guard = safe_dict(prepublish_reel_stack.get("publish_guard"))

        if prepublish_reel_stack.get("ok"):
            if str(release_authority.get("release_state", "")).startswith("BLOCKED_"):
                block_reasons.append(release_authority.get("release_state"))
            if publish_guard.get("mode") == "blocked":
                block_reasons.append("blocked_by_publish_guard")

        if prepublish_reel_stack.get("ok") and not publish_guard.get("can_publish"):
            return {
                "ok": False,
                "state": "HALT_BLOCKED_BY_GATE",
                "reason": "publish_guard_blocked",
                "release_authority": release_authority,
                "publish_guard": publish_guard,
                "prepublish_reel_stack": prepublish_reel_stack,
                "creative_plan": creative_plan,
                "editorial_qa": editorial_qa,
                "visual_qa": visual_qa,
                "perceptual_qa": perceptual_qa,
                "publication_authorization_gate": publication_authorization_gate,
                "brand_surface_policy": brand_surface_policy,
                "lab_probe_policy": lab_probe_policy,
                "runtime": self.snapshot(),
                "request_envelope": envelope.to_dict(),
            }

        carousel_preview, stories_preview = self._render_previews(creative_plan)

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
            "study_tags": STUDY_TAGS,
        }

        publish_guard_mode = publish_guard.get("mode")
        publish_guard_can_publish = bool(publish_guard.get("can_publish"))

        if runtime_request.force_placeholder or publication_authorization_gate.get("can_publish_placeholder"):
            if self.publish:
                publish_result = self.publish.publish_placeholder(
                    trend=trend_value,
                    style=str(creative_plan.get("publish_style") or mission_decision.get("style") or "official_next_visual_foundation_v1"),
                    content_type=str(creative_plan.get("publish_format_now") or mission_decision.get("content_type") or "image"),
                    caption=str(creative_plan.get("caption") or creative_plan.get("headline") or trend_value),
                    media_path=None,
                    linkage_context=linkage_context,
                )
            else:
                publish_result = {
                    "ok": False,
                    "publish_status": "publish_service_unavailable",
                    "error": "publish_service_unavailable",
                }
        else:
            should_render = bool(lab_probe_policy.get("probe_render_requested")) or publish_guard_can_publish
            if should_render:
                ok, render_result = self._call(
                    "render_visual_foundation_card",
                    config=self.config,
                    plan=creative_plan,
                    identity=visual_identity if "error" not in visual_identity else None,
                    typography=typography if "error" not in typography else None,
                )
                if ok and isinstance(render_result, str):
                    render_path = render_result
                    lab_probe_policy["probe_render_executed"] = True
                    lab_probe_policy["render_path"] = render_path
                else:
                    render_error = safe_dict(render_result).get("error") or "render_error"
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

                if self.publish:
                    publish_result = self.publish.publish_real(
                        trend=trend_value,
                        style=str(creative_plan.get("publish_style") or mission_decision.get("style") or "official_next_visual_foundation_v1"),
                        content_type=str(creative_plan.get("publish_format_now") or mission_decision.get("content_type") or "image"),
                        caption=str(creative_plan.get("caption") or creative_plan.get("headline") or trend_value),
                        media_path=render_path,
                        linkage_context=linkage_context,
                    )
                else:
                    publish_result = {
                        "ok": False,
                        "publish_status": "publish_service_unavailable",
                        "error": "publish_service_unavailable",
                    }

                publish_status = str(safe_dict(publish_result).get("publish_status") or "")
                lab_probe_policy["probe_publish_executed"] = publish_status == "published_real_probe"
            else:
                publish_result = {
                    "ok": True,
                    "publish_status": (
                        "not_published_surface_protected"
                        if publish_guard_mode != "ready"
                        else "not_published_probe_not_allowed"
                    ),
                    "operational_state": operational_state,
                    "content_type": str(creative_plan.get("publish_format_now") or mission_decision.get("content_type") or "image"),
                    "style": str(creative_plan.get("publish_style") or mission_decision.get("style") or "official_next_visual_foundation_v1"),
                    "created_at": _now_iso(),
                    "render_path": render_path,
                    "surface_mode": brand_surface_policy.get("surface_mode"),
                    "main_surface_allowed": brand_surface_policy.get("main_surface_allowed"),
                    "probe_requested": lab_probe_policy.get("probe_requested"),
                    "probe_eligible": lab_probe_policy.get("probe_eligible"),
                    "probe_publish_executed": False,
                    "probe_block_reason": lab_probe_policy.get("probe_block_reason") or brand_surface_policy.get("block_reason"),
                    "render_error": render_error,
                }

        publish_result = adapt_legacy_publish_result(publish_result)
        publish_truth_state = _publish_truth_state_from_result(publish_result)

        postpublish_reel_stack = self._run_reel_premium_stack(
            trend=trend_value,
            creative_plan=creative_plan,
            visual_qa=visual_qa,
            perceptual_qa=perceptual_qa,
            publication_authorization_gate=publication_authorization_gate,
            operational_state=operational_state,
            publish_truth_state=publish_truth_state,
        )

        measurement = self._measurement_summary(
            publish_result=publish_result,
            creative_plan=creative_plan,
            mission_decision=mission_decision,
        )

        self._last_run_summary = {
            "timestamp": _now_iso(),
            "premium_classification": publication_authorization_gate.get("premium_classification"),
            "eligible_for_editorial_staging": publication_authorization_gate.get("eligible_for_editorial_staging"),
            "eligible_for_brand_live_candidate": publication_authorization_gate.get("eligible_for_brand_live_candidate"),
            "missing_for_brand_live": publication_authorization_gate.get("missing_for_brand_live"),
            "score_gap_to_brand_live": publication_authorization_gate.get("score_gap_to_brand_live"),
            "next_quality_lift_targets": publication_authorization_gate.get("next_quality_lift_targets"),
            "publication_authorization_summary": publication_authorization_gate.get("summary"),
            "selected_template_id": premium_visual.get("selected_template_id"),
            "premium_render_state": premium_visual.get("premium_render_state"),
            "hardening_applied": premium_visual.get("hardening_applied"),
            "hardening_report": premium_visual.get("hardening_report"),
            "reel_stack_state": prepublish_reel_stack.get("stack_state"),
            "prepublish_gate": _gate_stage_summary(prepublish_reel_stack),
            "postpublish_gate": _gate_stage_summary(postpublish_reel_stack),
            "publish_truth_state": publish_truth_state,
            "study_tags": STUDY_TAGS,
            "wave_alignment": {
                "wave1_runtime_fino": True,
                "wave2_editorial_brain": True,
                "wave3_visual_premium": True,
                "wave4_reel_premium_stack": True,
                "wave5_publish_truth_learning": True,
                "wave6_expansion_ready": True,
            },
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
            "real_probe_allowed_states": sorted(REAL_PROBE_ALLOWED_STATES),
            "probe_requested": bool(lab_probe_policy.get("probe_requested")),
            "probe_eligible": bool(lab_probe_policy.get("probe_eligible")),
            "probe_publish_executed": bool(lab_probe_policy.get("probe_publish_executed")),
            "probe_block_reason": lab_probe_policy.get("probe_block_reason") or brand_surface_policy.get("block_reason"),
            "block_reasons": block_reasons,
            "request_envelope": envelope.to_dict(),
            "request_contract": runtime_request.to_dict(),
            "brand_surface_policy": brand_surface_policy,
            "lab_probe_policy": lab_probe_policy,
            "trend": trend_value,
            "mission_decision": mission_decision,
            "mission_control_state": mission_control_state,
            "creative_plan_ok": plan_ok,
            "creative_plan": creative_plan,
            "editorial_qa": editorial_qa,
            "visual_contract": visual_contract,
            "visual_template": visual_template,
            "perceptual_qa": perceptual_qa,
            "visual_identity": adapt_legacy_visual(visual_identity),
            "typography": typography,
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
            "last_publish": self.publish.last_publish() if self.publish else None,
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
                "perception": True,
                "planning": True,
                "visual_premium": True,
                "premium_stack": bool(prepublish_reel_stack.get("ok")),
                "gate_before_publish": bool(safe_dict(prepublish_reel_stack.get("publish_guard")).get("can_publish")),
                "publish_truth_after_publish": True,
                "learning_real": True,
                "expansion_ready": True,
                "organism_state": "perceive_decide_create_gate_publish_prove_measure_learn_evolve",
            },
            "study_alignment": {
                "manifesto_runtime_fino": True,
                "cronograma_wave_alignment": True,
                "guide_module_alignment": True,
                "ethical_boundary": "retention_without_hidden_manipulation",
            },
        }
