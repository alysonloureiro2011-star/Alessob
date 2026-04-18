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
