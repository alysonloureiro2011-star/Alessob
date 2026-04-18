from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from .authorized_payload_resolver import resolve_authorized_payload
from .config import AceNextConfig
try:
    from .prepublish_rewrite_engine import PrePublishRewriteEngine
except Exception:  # pragma: no cover
    PrePublishRewriteEngine = None
from .dignity_adapter_runtime import run_dignity_adapter
from .reflection_adapter_runtime import run_reflection_adapter
from .runtime_adapters import (
    adapt_legacy_mission_decision,
    adapt_legacy_publish_result,
    adapt_legacy_visual,
)
from .runtime_bootstrap import bootstrap_capabilities
from .runtime_contracts import (
    build_runtime_execution_envelope,
    build_runtime_request,
    normalize_probe_state,
    normalize_trend,
    safe_bool,
    safe_dict,
)
from .runtime_phase_absorption import build_runtime_phase_absorption
from .runtime_registry import capability_registry_snapshot, resolve_capability
from .serial_adapter_runtime import run_serial_adapter
from .trend_input_guard import sanitize_trend_input
from .trend_radar import TrendRadar
from .visual_gate_adapter_runtime import run_visual_gate_adapter

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
    "rhythm": "cadence_450_1200_850_1500_300",
    "naturalism": "micro_expression_grain_breathing_foley",
    "mab": "exploration_vs_exploitation",
    "attention_engineering": "save_share_replay_retention_priority",
    "multiplatform": "format_distribution_publish_decoupled",
    "cinematic": "9x16_rule_of_thirds_bokeh_color_foley_ducking",
    "priority_signals": "shares_saves_completion_watch_time",
}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now_utc().isoformat()


def _short_error_summary(value: Any, limit: int = 240) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return text if len(text) <= limit else f"{text[: limit - 3]}..."


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


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _first_path(paths: Any) -> str | None:
    if not isinstance(paths, list):
        return None
    for item in paths:
        text = _clean_text(item)
        if text:
            return text
    return None


class OfficialRuntime:
    def __init__(self, config: AceNextConfig) -> None:
        self.config = config
        self._boot = bootstrap_capabilities()
        self._last_run_summary: dict[str, Any] = {}
        self._resolution_cache: dict[str, dict[str, Any]] = {}

        publish_cls = self._symbol("PublishService")
        self.publish = publish_cls(config) if publish_cls else None
        self.trend_radar = TrendRadar()
        self.phase_absorption = build_runtime_phase_absorption()
        self.prepublish_rewrite_engine = PrePublishRewriteEngine() if PrePublishRewriteEngine else None

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
            return True, symbol(*args, **kwargs)
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

    def _safe_import_symbol(self, module_path: str, symbol_name: str):
        try:
            module = __import__(module_path, fromlist=[symbol_name])
            return getattr(module, symbol_name)
        except Exception:
            return None

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

    def _llm_orchestrator_status(self) -> dict[str, Any]:
        status_fn = self._safe_import_symbol("ace_next.llm_orchestrator", "llm_orchestrator_status")
        if status_fn is None:
            return {"ok": False, "reason": "llm_orchestrator_unavailable"}
        try:
            result = status_fn()
            parsed = safe_dict(result)
            parsed.setdefault("ok", True)
            return parsed
        except Exception as exc:
            return {"ok": False, "reason": f"llm_orchestrator_status_error: {type(exc).__name__}: {exc}"}

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
            "llm_orchestrator_status": self._llm_orchestrator_status(),
            "study_tags": STUDY_TAGS,
            "runtime_design": {
                "mode": "sovereign_runtime_v2",
                "contracts": True,
                "registry": True,
                "adapters": True,
                "bootstrap": True,
                "legacy_compatibility": True,
                "trend_input_guard": True,
                "authorized_payload_resolver": True,
                "super_orchestrator_compatible": True,
                "repair_loop": True,
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
    # EDITORIAL / SERIAL / REFLECTION HELPERS
    # ---------------------------------------------------------
    def _mission_approval_required(self) -> bool:
        return safe_bool(os.environ.get("ACE_REQUIRE_MISSION_APPROVAL"), False)

    def _planner_overrides_from_mission_decision(self, mission_decision: dict[str, Any] | None) -> dict[str, Any]:
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

    def _editorial_brain_or_fallback(
        self,
        *,
        trend: str,
        recent_signal_score: float | None,
        env_flags: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        recent_memory = self._recent_memory_for_planner(limit=5)
        brain_cls = self._safe_import_symbol("ace_next.editorial_brain_v2", "EditorialBrainV2")
        if brain_cls is None:
            return {}, {}, {"ok": False, "used": False, "state": "editorial_brain_unavailable"}

        try:
            brain_result = safe_dict(
                brain_cls().run(
                    trend=trend,
                    format_hint=None,
                    recent_signal_score=recent_signal_score,
                    queue_state=self._runtime_queue_state(),
                    signal_context={"source": "official_runtime", "mode": "run"},
                    brand_context={
                        "brand_surface_mode": env_flags.get("ACE_BRAND_SURFACE_MODE"),
                        "brand_live_allowed": False,
                    },
                    recent_memory=recent_memory,
                )
                or {}
            )
            mission = safe_dict(brain_result.get("mission_decision"))
            creative_plan = safe_dict(brain_result.get("creative_plan"))
            if mission and creative_plan:
                mission.setdefault("raw", mission)
                creative_plan.setdefault("study_tags", STUDY_TAGS)
                creative_plan.setdefault("serial_continuity_hint", bool(recent_memory))
                creative_plan.setdefault("attention_target", "save_share_replay_retention")
                creative_plan.setdefault("ethical_boundary", "no_hidden_manipulation")
                return mission, creative_plan, {
                    "ok": True,
                    "state": brain_result.get("brain_state") or "editorial_brain_v2_ready",
                    "used": True,
                    "result": brain_result,
                }
            return {}, {}, {"ok": False, "used": False, "state": "editorial_brain_result_incomplete"}
        except Exception as exc:
            return {}, {}, {"ok": False, "used": False, "state": f"editorial_brain_error: {type(exc).__name__}: {exc}"}

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

    def _llm_orchestrator_instance(self):
        cls = self._safe_import_symbol("ace_next.llm_orchestrator", "LLMOrchestrator")
        if cls is None:
            return None
        try:
            return cls()
        except Exception:
            return None

    def _seo_social_engine_instance(self):
        cls = self._safe_import_symbol("ace_next.seo_social_engine", "SeoSocialEngine")
        if cls is None:
            return None
        try:
            return cls()
        except Exception:
            return None

    def _run_prepublish_rewrite(
        self,
        *,
        trend: str,
        creative_plan: dict[str, Any],
        editorial_qa: dict[str, Any],
    ) -> dict[str, Any]:
        if self.prepublish_rewrite_engine is None:
            return {
                "ok": False,
                "rewrite_needed": False,
                "rewrite_applied": False,
                "post_rewrite_state": "rewrite_module_unavailable",
                "creative_plan": creative_plan,
                "seo_social": {},
            }

        try:
            result = self.prepublish_rewrite_engine.rewrite(
                creative_plan=creative_plan,
                trend=trend,
                editorial_qa=editorial_qa,
                llm_orchestrator=self._llm_orchestrator_instance(),
                seo_social_engine=self._seo_social_engine_instance(),
                platform="instagram",
            )
            result = safe_dict(result)
            result["creative_plan"] = safe_dict(result.get("creative_plan")) or creative_plan
            result["seo_social"] = safe_dict(result.get("seo_social"))
            return result
        except Exception as exc:
            return {
                "ok": False,
                "rewrite_needed": False,
                "rewrite_applied": False,
                "post_rewrite_state": "rewrite_error",
                "rewrite_error": f"{type(exc).__name__}: {exc}",
                "creative_plan": creative_plan,
                "seo_social": {},
            }

    def _serial_continuity_summary(self, creative_plan: dict[str, Any]) -> dict[str, Any]:
        merged_data: dict[str, Any] = {}
        engine_state = None

        try:
            build_serial_continuity = self._safe_import_symbol(
                "ace_next.serial_continuity_engine",
                "build_serial_continuity",
            )
            if build_serial_continuity is not None:
                engine_result = safe_dict(
                    build_serial_continuity(
                        creative_plan,
                        recent_memory=self._recent_memory_for_planner(limit=5),
                    )
                    or {}
                )
                if engine_result:
                    engine_state = "serial_continuity_engine_ready" if engine_result.get("ok") else "serial_continuity_engine_fallback"
                    merged_data.update(engine_result)
        except Exception:
            engine_state = "serial_continuity_engine_error"

        try:
            adapter_result = safe_dict(
                run_serial_adapter(
                    {
                        "creative_plan": creative_plan,
                        "recent_memory": self._recent_memory_for_planner(limit=5),
                    }
                )
                or {}
            )
            adapter_data = safe_dict(adapter_result.get("data"))

if adapter_data:
                merged_data.update(adapter_data)

            if merged_data:
                current_serial = safe_dict(creative_plan.get("serial_continuity"))
                creative_plan["serial_continuity"] = {**current_serial, **merged_data}
                if merged_data.get("next_episode_seed") and not creative_plan.get("series_next"):
                    creative_plan["series_next"] = merged_data.get("next_episode_seed")

            return {
                "ok": bool(adapter_result.get("ok", True) or merged_data),
                "state": adapter_result.get("state") or engine_state or "serial_adapter_ready",
                "data": merged_data,
                "meta": {**safe_dict(adapter_result.get("meta")), "engine_state": engine_state},
            }
        except Exception as exc:
            return {
                "ok": bool(merged_data),
                "state": engine_state or "serial_adapter_error",
                "data": merged_data,
                "meta": {"error": f"{type(exc).__name__}: {exc}", "engine_state": engine_state},
            }

    def _reflection_adapter_summary(
        self,
        *,
        creative_plan: dict[str, Any],
        measurement: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            real_metrics = safe_dict(safe_dict(measurement.get("performance_ingest")).get("real_metrics"))
            adapter_result = safe_dict(
                run_reflection_adapter(
                    {
                        "creative_plan": creative_plan,
                        "real_metrics": real_metrics,
                        "recommendation_engine": safe_dict(measurement.get("recommendation_engine")),
                        "attention_metrics": safe_dict(measurement.get("attention_metrics")),
                    }
                )
                or {}
            )
        except Exception as exc:
            adapter_result = {
                "ok": False,
                "state": "reflection_adapter_error",
                "data": {},
                "meta": {"error": f"{type(exc).__name__}: {exc}"},
            }

        engine_cls = self._safe_import_symbol("ace_next.reflection_engine", "ReflectionEngine")
        if engine_cls is not None:
            try:
                engine_result = safe_dict(
                    engine_cls().run(
                        creative_plan=creative_plan,
                        real_metrics=safe_dict(safe_dict(measurement.get("performance_ingest")).get("real_metrics")),
                        recommendation_engine=safe_dict(measurement.get("recommendation_engine")),
                        attention_metrics=safe_dict(measurement.get("attention_metrics")),
                    )
                    or {}
                )
                if engine_result:
                    adapter_result["engine_result"] = engine_result
                    adapter_result["data"] = {**safe_dict(adapter_result.get("data")), **engine_result}
            except Exception:
                pass

        return adapter_result

    # ---------------------------------------------------------
    # VISUAL / PAYLOAD / GATES
    # ---------------------------------------------------------
    def _visual_foundation(
        self,
        plan_dict: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
        visual_identity: dict[str, Any] = {}
        typography: dict[str, Any] = {}
        visual_contract: dict[str, Any] = {}
        visual_template: dict[str, Any] = {}
        perceptual_qa: dict[str, Any] = {}
        visual_qa: dict[str, Any] = {}

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

        if (
            visual_identity
            and typography
            and visual_contract
            and visual_template
            and "error" not in visual_identity
            and "error" not in typography
            and "error" not in visual_contract
            and "error" not in visual_template
        ):
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
            premium_visual.setdefault(
                "study_alignment",
                {
                    "pattern_interrupt_visual": True,
                    "playwright_official_path": True,
                    "premium_layout_variation": True,
                },
            )
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

    def _resolve_authorized_payload(
        self,
        *,
        creative_plan: dict[str, Any],
        premium_visual: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        hardening_report = safe_dict(premium_visual.get("hardening_report"))
        premium_metrics = safe_dict(premium_visual.get("metrics"))

        hardened_payload = safe_dict(
            hardening_report.get("hardened_payload")
            or premium_visual.get("hardened_visible_payload")
            or premium_metrics.get("render_payload_used")
        )
        render_payload_used = safe_dict(
            hardening_report.get("render_payload_used")
            or premium_metrics.get("render_payload_used")
        )

        resolution = resolve_authorized_payload(
            creative_plan,
            hardened_payload=hardened_payload or None,
            render_payload_used=render_payload_used or None,
            strategic_format=str(
                creative_plan.get("publish_format_now")
                or creative_plan.get("strategic_target_format")
                or creative_plan.get("format_recommendation")
                or "image"
            ),
            template_id=str(
                premium_visual.get("selected_template_id")
                or hardening_report.get("selected_template_id")
                or creative_plan.get("template_id")
                or ""
            )
            or None,
            capture_mode="safe",
        )

        authorized_payload = safe_dict(resolution.get("authorized_payload"))
        updated_plan = dict(creative_plan)

        if authorized_payload:
            updated_plan["headline"] = authorized_payload.get("headline") or updated_plan.get("headline")
            updated_plan["hook"] = authorized_payload.get("hook") or updated_plan.get("hook")
            updated_plan["body"] = authorized_payload.get("body") or updated_plan.get("body")
            updated_plan["cta"] = authorized_payload.get("cta") or updated_plan.get("cta")
            updated_plan["caption"] = authorized_payload.get("caption") or updated_plan.get("caption")
            updated_plan["support_points"] = authorized_payload.get("support_points") or updated_plan.get("support_points") or []
            updated_plan["publish_format_now"] = authorized_payload.get("format") or updated_plan.get("publish_format_now")


updated_plan["authorized_payload"] = authorized_payload
            updated_plan["authority_payload_source"] = resolution.get("authorized_source")
            updated_plan["authorized_payload_budget"] = resolution.get("budget")
            updated_plan["authorized_payload_changed_fields"] = resolution.get("changed_fields") or []

        merged_hardener = dict(hardening_report)
        merged_hardener["authorized_payload"] = authorized_payload
        merged_hardener["authority_payload_source"] = resolution.get("authorized_source")
        merged_hardener["changed_fields"] = resolution.get("changed_fields") or []
        merged_hardener["changed_fields_count"] = resolution.get("changed_fields_count")
        merged_hardener["authorized_payload_budget"] = resolution.get("budget")
        merged_hardener["hardening_report"] = safe_dict(resolution.get("hardening_report"))

        return updated_plan, resolution, merged_hardener

    def _build_visual_gate_contract(
        self,
        *,
        creative_plan: dict[str, Any],
        visual_template: dict[str, Any],
        authorized_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = safe_dict(authorized_payload) or {
            "headline": creative_plan.get("headline"),
            "hook": creative_plan.get("hook"),
            "body": creative_plan.get("body"),
            "cta": creative_plan.get("cta"),
            "support_points": creative_plan.get("support_points") or [],
            "format": (
                creative_plan.get("publish_format_now")
                or creative_plan.get("strategic_target_format")
                or "image"
            ),
        }
        return {
            "brand_system": {"text_contrast_policy": "premium_high_contrast"},
            "template_spec": {
                "template_id": visual_template.get("template_id"),
                "premium_tier": visual_template.get("premium_tier"),
                "html_ready": visual_template.get("html_ready"),
                "block_order": visual_template.get("block_order"),
                "strategic_format": payload.get("format") or "image",
            },
            "layout_payload": {"display_payload": payload},
            "gate_payload": {"format": payload.get("format") or "image"},
        }

    def _visual_gate_adapter_summary(
        self,
        *,
        creative_plan: dict[str, Any],
        visual_template: dict[str, Any],
        authorized_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            contract = self._build_visual_gate_contract(
                creative_plan=creative_plan,
                visual_template=visual_template,
                authorized_payload=authorized_payload,
            )
            return safe_dict(run_visual_gate_adapter({"contract": contract}) or {})
        except Exception as exc:
            return {
                "ok": False,
                "state": "visual_gate_adapter_error",
                "data": {},
                "meta": {"error": f"{type(exc).__name__}: {exc}"},
            }

    def _dignity_adapter_summary(
        self,
        *,
        creative_plan: dict[str, Any],
        visual_qa: dict[str, Any],
        hierarchy_gate: dict[str, Any],
        visual_template: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            return safe_dict(
                run_dignity_adapter(
                    {
                        "creative_plan": creative_plan,
                        "visual_qa": visual_qa,
                        "hierarchy_gate": hierarchy_gate,
                        "template_meta": visual_template,
                    }
                )
                or {}
            )
        except Exception as exc:
            return {
                "ok": False,
                "state": "dignity_adapter_error",
                "data": {},
                "meta": {"error": f"{type(exc).__name__}: {exc}"},
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
            "authority_payload_source": None,
        }
        return rubric_engine, brand_veto_gate, publication_authorization_gate

    def _run_authorization_stack_base(
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
        return self.phase_absorption.apply_phase5_authorization_stack(
            force_placeholder=force_placeholder,
            plan_dict=plan_dict,
            editorial_qa=editorial_qa,
            visual_qa=visual_qa,
            perceptual_qa=perceptual_qa,
            env_flags=env_flags,
            request_flags=request_flags,
            staging_hardener=staging_hardener,
            fallback_runner=self._run_authorization_stack_base,
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
