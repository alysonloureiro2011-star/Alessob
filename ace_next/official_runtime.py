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

