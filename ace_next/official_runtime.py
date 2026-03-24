from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from .auth_store import load_instagram_auth, sync_instagram_token_sources
from .brand_surface_isolation import resolve_brand_surface_policy
from .config import AceNextConfig
from .creative_planner import build_creative_plan
from .editorial_rubric import evaluate_editorial_quality
from .lab_probe_policy import resolve_lab_probe_policy
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

AUTH_STACK_IMPORT_ERROR: str | None = None
MEASUREMENT_STACK_IMPORT_ERROR: str | None = None
REAL_PROBE_ALLOWED_STATES = ["internal_lab", "editorial_staging"]

try:
    from .rubric_engine import evaluate_rubric_engine
    from .brand_veto_gate import evaluate_brand_veto_gate
    from .publication_authorization_gate import authorize_publication
except Exception as exc:
    AUTH_STACK_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
    evaluate_rubric_engine = None
    evaluate_brand_veto_gate = None
    authorize_publication = None

try:
    from .performance_store import PerformanceStore
    from .learning_loop import build_learning_loop_summary
    from .post_performance_contract import build_post_performance_contract
    from .performance_ingest import collect_real_performance_metrics
    from .reflection_memory import build_reflection_memory
    from .attention_metrics import build_attention_metrics
    from .experiment_registry import ExperimentRegistry, build_experiment_record
    from .episodic_performance_memory import EpisodicPerformanceMemory, build_episode_record
    from .performance_summary import build_performance_summary
    from .resonance_engine import build_resonance_engine
    from .reward_prediction_layer import build_reward_prediction
    from .thompson_sampler import build_thompson_sampler
    from .evidence_interpreter import build_evidence_interpreter
    from .experiment_resolution_engine import build_experiment_resolution
    from .recommendation_engine import build_recommendation_engine
except Exception as exc:
    MEASUREMENT_STACK_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
    PerformanceStore = None
    build_learning_loop_summary = None
    build_post_performance_contract = None
    collect_real_performance_metrics = None
    build_reflection_memory = None
    build_attention_metrics = None
    ExperimentRegistry = None
    build_experiment_record = None
    EpisodicPerformanceMemory = None
    build_episode_record = None
    build_performance_summary = None
    build_resonance_engine = None
    build_reward_prediction = None
    build_thompson_sampler = None
    build_evidence_interpreter = None
    build_experiment_resolution = None
    build_recommendation_engine = None


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _normalize_probe_state(value: str | None) -> str:
    normalized = str(value or "auto").strip().lower()
    if normalized in {"auto", "internal_lab", "editorial_staging", "brand_live"}:
        return normalized
    return "auto"


def _as_bool_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


class OfficialRuntime:
    def __init__(self, config: AceNextConfig):
        self.config = config
        self.publish = PublishService(config)
        self._boot_sync()

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

    def _performance_store_summary(self) -> dict[str, Any]:
        if MEASUREMENT_STACK_IMPORT_ERROR or PerformanceStore is None:
            return {"ok": False, "error": MEASUREMENT_STACK_IMPORT_ERROR or "measurement_stack_unavailable"}
        try:
            return PerformanceStore(self.config).summary().to_dict()
        except Exception as exc:
            return {"ok": False, "error": f"performance_store_summary_error: {type(exc).__name__}: {exc}"}

    def _experiment_registry_summary(self) -> dict[str, Any]:
        if MEASUREMENT_STACK_IMPORT_ERROR or ExperimentRegistry is None:
            return {"ok": False, "error": MEASUREMENT_STACK_IMPORT_ERROR or "measurement_stack_unavailable"}
        try:
            return ExperimentRegistry(self.config).summary().to_dict()
        except Exception as exc:
            return {"ok": False, "error": f"experiment_registry_summary_error: {type(exc).__name__}: {exc}"}

    def _episodic_memory_summary(self) -> dict[str, Any]:
        if MEASUREMENT_STACK_IMPORT_ERROR or EpisodicPerformanceMemory is None:
            return {"ok": False, "error": MEASUREMENT_STACK_IMPORT_ERROR or "measurement_stack_unavailable"}
        try:
            return EpisodicPerformanceMemory(self.config).summary().to_dict()
        except Exception as exc:
            return {"ok": False, "error": f"episodic_memory_summary_error: {type(exc).__name__}: {exc}"}

    def snapshot(self) -> dict:
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
            "experiment_registry": self._experiment_registry_summary(),
            "episodic_performance_memory": self._episodic_memory_summary(),
            "real_probe_route_supported": True,
            "real_probe_allowed_states": REAL_PROBE_ALLOWED_STATES,
            "brand_live_allowed": False,
            "brand_surface_mode": env_flags.get("ACE_BRAND_SURFACE_MODE"),
            "brand_surface_flags": env_flags,
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

    def _measurement_fallback(self, *, reason: str):
        post_performance_contract = {"ok": False, "error": reason}
        performance_ingest = {
            "ok": False,
            "attempted": False,
            "collection_success": False,
            "source_status": "ingest_error",
            "real_metrics": {"source_status": "ingest_error", "source_reason": reason, "errors": [reason]},
            "attention_inputs": {},
            "errors": [reason],
            "raw": {},
        }
        attention_metrics = {
            "ok": False,
            "source_status": "ingest_error",
            "breakdown": {},
            "available_inputs": [],
            "notes": [reason],
        }
        resonance_engine = {
            "ok": False,
            "resonance_score": None,
            "reasons": [reason],
        }
        reward_prediction = {
            "ok": False,
            "reward_prediction_score": None,
            "reasons": [reason],
        }
        thompson_sampler = {
            "ok": False,
            "selected_variant": None,
            "confidence_level": "low",
            "decision_state": "collecting",
            "posterior_mean": None,
            "winner_candidate": False,
            "reasons": [reason],
        }
        decision_core_summary = {
            "ok": False,
            "resonance_score": None,
            "reward_prediction_score": None,
            "selected_variant": None,
            "confidence_level": "low",
            "experiment_decision_state": "collecting",
            "posterior_mean": None,
            "winner_candidate": False,
            "reasons": [reason],
        }
        evidence_interpreter = {
            "ok": False,
            "evidence_state": "ingest_error",
            "evidence_strength": "none",
            "evidence_ready_for_resolution": False,
            "evidence_reasons": [reason],
            "bridge_state": "no_receipt",
        }
        experiment_resolution = {
            "ok": False,
            "resolution_state": "collecting",
            "can_resolve": False,
            "winner_candidate": False,
            "loser_candidate": False,
            "keep_collecting": True,
            "confidence_level": "low",
            "resolution_reason": reason,
            "promotion_readiness": "not_ready",
        }
        recommendation_engine = {
            "ok": False,
            "recommended_action": "repeat_probe",
            "action_priority": "low",
            "recommendation_reason": reason,
            "next_best_step": "restaurar a base antes de interpretar evidência",
            "safe_to_repeat": False,
            "safe_to_promote_to_editorial_staging": False,
            "requires_human_review": True,
        }
        wave10_summary = {
            "ok": False,
            "evidence_state": "ingest_error",
            "resolution_state": "collecting",
            "recommended_action": "repeat_probe",
        }
        wave11_summary = {
            "ok": False,
            "brand_live_allowed": False,
            "evidence_state": "no_receipt",
            "has_receipt": False,
            "has_media_id": False,
            "has_permalink": False,
            "can_resolve": False,
            "recommended_action": "repeat_probe",
            "next_best_step": "restaurar a base antes de interpretar evidência",
        }
        experiment_registry = {"ok": False, "error": reason}
        episodic_performance_memory = {"ok": False, "error": reason}
        reflection_memory = {
            "ok": False,
            "status": "ingest_error",
            "notes": [reason],
            "guardrails": {
                "can_change_brand_policy": False,
                "can_change_editorial_policy": False,
                "can_change_visual_policy": False,
                "can_authorize_brand_live": False,
                "can_autopublish": False,
            },
        }
        learning_loop = {
            "ok": False,
            "error": reason,
            "insight_control": {
                "can_record": False,
                "can_consolidate": False,
                "can_suggest": False,
                "can_change_brand_policy": False,
                "can_change_editorial_policy": False,
                "can_change_visual_policy": False,
                "can_autopublish_brand_live": False,
            },
        }
        performance_summary = {"ok": False, "error": reason}
        return (
            post_performance_contract,
            performance_ingest,
            attention_metrics,
            resonance_engine,
            reward_prediction,
            thompson_sampler,
            decision_core_summary,
            evidence_interpreter,
            experiment_resolution,
            recommendation_engine,
            wave10_summary,
            wave11_summary,
            experiment_registry,
            episodic_performance_memory,
            reflection_memory,
            learning_loop,
            performance_summary,
        )

    def _run_measurement_core(
        self,
        *,
        trend: str,
        operational_state: str,
        brand_live_allowed: bool,
        creative_plan: dict[str, Any],
        editorial_qa: dict[str, Any],
        visual_qa: dict[str, Any],
        visual_template: dict[str, Any],
        rubric_engine: dict[str, Any],
        publication_authorization_gate: dict[str, Any],
        publish_result: dict[str, Any] | None,
        probe_context: dict[str, Any],
    ):
        if (
            MEASUREMENT_STACK_IMPORT_ERROR
            or not PerformanceStore
            or not build_learning_loop_summary
            or not build_post_performance_contract
            or not collect_real_performance_metrics
            or not build_reflection_memory
            or not build_attention_metrics
            or not ExperimentRegistry
            or not build_experiment_record
            or not EpisodicPerformanceMemory
            or not build_episode_record
            or not build_performance_summary
            or not build_resonance_engine
            or not build_reward_prediction
            or not build_thompson_sampler
            or not build_evidence_interpreter
            or not build_experiment_resolution
            or not build_recommendation_engine
        ):
            fallback = self._measurement_fallback(
                reason=f"measurement_stack_import_error: {MEASUREMENT_STACK_IMPORT_ERROR or 'unknown'}"
            )
            return (*fallback, {"ok": False, "error": MEASUREMENT_STACK_IMPORT_ERROR or "measurement_stack_unavailable"})

        try:
            record = build_post_performance_contract(
                trend=trend,
                operational_state=operational_state,
                brand_live_allowed=brand_live_allowed,
                creative_plan=creative_plan,
                editorial_qa=editorial_qa,
                visual_qa=visual_qa,
                publish_result=publish_result,
                publication_authorization_gate=publication_authorization_gate,
            )
            record["probe_context"] = dict(probe_context)
            record["visual_template"] = visual_template
            record["rubric_engine"] = rubric_engine

            performance_ingest = collect_real_performance_metrics(
                config=self.config,
                publish_result=publish_result,
            )
            real_metrics = dict(performance_ingest.get("real_metrics") or {})
            attention_inputs = dict(performance_ingest.get("attention_inputs") or {})
            attention_metrics = build_attention_metrics(
                real_metrics=real_metrics,
                attention_inputs=attention_inputs,
            )

            record["real_metrics"] = real_metrics
            record["performance_ingest"] = performance_ingest
            record["attention_metrics"] = attention_metrics

            resonance_engine = build_resonance_engine(record=record)
            reward_prediction = build_reward_prediction(
                record=record,
                resonance_engine=resonance_engine,
            )
            thompson_sampler = build_thompson_sampler(
                record=record,
                reward_prediction=reward_prediction,
                conservative_mode=True,
            )
            decision_core_summary = {
                "ok": True,
                "resonance_score": resonance_engine.get("resonance_score"),
                "reward_prediction_score": reward_prediction.get("reward_prediction_score"),
                "selected_variant": thompson_sampler.get("selected_variant"),
                "confidence_level": thompson_sampler.get("confidence_level"),
                "experiment_decision_state": thompson_sampler.get("decision_state"),
                "posterior_mean": thompson_sampler.get("posterior_mean"),
                "winner_candidate": thompson_sampler.get("winner_candidate"),
                "conservative_mode": thompson_sampler.get("conservative_mode"),
                "reasons": [
                    "decision core deriva de módulos auditáveis",
                    "nenhum sorteio aleatório foi usado",
                ],
            }

            record["resonance_engine"] = resonance_engine
            record["reward_prediction"] = reward_prediction
            record["sampler_decision"] = thompson_sampler
            record["decision_core_summary"] = decision_core_summary

            evidence_interpreter = build_evidence_interpreter(record=record)

            experiment_resolution = build_experiment_resolution(
                experiment_context=dict(record.get("experiment_registry") or {}),
                thompson_sampler=thompson_sampler,
                reward_prediction=reward_prediction,
                attention_metrics=attention_metrics,
                evidence_interpreter=evidence_interpreter,
            )

            recommendation_engine = build_recommendation_engine(
                evidence_interpreter=evidence_interpreter,
                experiment_resolution=experiment_resolution,
                resonance_engine=resonance_engine,
                reward_prediction=reward_prediction,
                attention_metrics=attention_metrics,
                operational_state=operational_state,
            )

            wave10_summary = {
                "ok": True,
                "evidence_state": evidence_interpreter.get("evidence_state"),
                "resolution_state": experiment_resolution.get("resolution_state"),
                "recommended_action": recommendation_engine.get("recommended_action"),
            }

            wave11_summary = {
                "ok": True,
                "brand_live_allowed": False,
                "evidence_state": evidence_interpreter.get("evidence_state"),
                "has_receipt": evidence_interpreter.get("has_real_receipt"),
                "has_media_id": evidence_interpreter.get("has_media_id"),
                "has_permalink": evidence_interpreter.get("has_permalink"),
                "can_resolve": experiment_resolution.get("can_resolve"),
                "recommended_action": recommendation_engine.get("recommended_action"),
                "next_best_step": recommendation_engine.get("next_best_step"),
            }

            record["evidence_interpreter"] = evidence_interpreter
            record["experiment_resolution"] = experiment_resolution
            record["recommendation_engine"] = recommendation_engine
            record["wave10_summary"] = wave10_summary
            record["wave11_summary"] = wave11_summary
            record["resolution_context"] = {
                "evidence_state": evidence_interpreter.get("evidence_state"),
                "evidence_strength": evidence_interpreter.get("evidence_strength"),
                "resolution_state": experiment_resolution.get("resolution_state"),
                "recommended_action": recommendation_engine.get("recommended_action"),
            }
            record["publish_receipt_bridge"] = {
                "publish_status": (record.get("publish_result") or {}).get("publish_status"),
                "receipt_id": (record.get("publish_result") or {}).get("receipt_id"),
                "media_id": (record.get("publish_result") or {}).get("media_id"),
                "permalink": (record.get("publish_result") or {}).get("permalink"),
                "content_type": (record.get("publish_result") or {}).get("content_type"),
                "style": (record.get("publish_result") or {}).get("style"),
                "created_at": (record.get("publish_result") or {}).get("created_at"),
            }
            record["evidence_bridge"] = {
                "has_real_receipt": bool((record.get("publish_result") or {}).get("receipt_id")),
                "has_media_id": bool((record.get("publish_result") or {}).get("media_id")),
                "has_permalink": bool((record.get("publish_result") or {}).get("permalink")),
                "latest_real_metrics_status": real_metrics.get("source_status"),
                "latest_source_status": real_metrics.get("source_status"),
                "evidence_bridge_state": evidence_interpreter.get("bridge_state"),
            }
            record["brand_surface_policy"] = probe_context.get("brand_surface_policy")
            record["lab_probe_policy"] = probe_context.get("lab_probe_policy")

            record["post_performance"] = {
                "status": real_metrics.get("source_status"),
                "source": real_metrics.get("source_endpoint"),
                "metrics": {
                    "impressions": real_metrics.get("impressions"),
                    "reach": real_metrics.get("reach"),
                    "likes": real_metrics.get("likes"),
                    "comments": real_metrics.get("comments"),
                    "saves": real_metrics.get("saves"),
                    "shares": real_metrics.get("shares"),
                    "engagement_proxy": real_metrics.get("engagement_proxy"),
                    "attention_score": (
                        (attention_metrics.get("breakdown") or {}).get("attention_score")
                        if isinstance(attention_metrics, dict)
                        else None
                    ),
                },
                "notes": [
                    "dados de performance baseados apenas em coleta real ou ausência real de dados",
                    str(real_metrics.get("source_reason") or ""),
                ],
            }

            experiment_record = build_experiment_record(record=record)
            experiment_store = ExperimentRegistry(self.config)
            experiment_registry = experiment_store.upsert_experiment(experiment_record)
            record["experiment_registry"] = experiment_record

            episode_record = build_episode_record(record=record)
            episode_store = EpisodicPerformanceMemory(self.config)
            episodic_performance_memory = episode_store.upsert_episode(episode_record)
            record["episodic_performance_memory"] = episode_record

            reflection_memory = build_reflection_memory(record=record)
            record["reflection_memory"] = reflection_memory

            store = PerformanceStore(self.config)
            performance_store = store.upsert_record(record)
            records = store.list_records(limit=30)

            learning_loop = build_learning_loop_summary(
                records=records,
                latest_record=record,
            )
            performance_summary = build_performance_summary(
                performance_store=performance_store,
                learning_loop=learning_loop,
                experiment_registry=experiment_registry,
                episodic_performance_memory=episodic_performance_memory,
                attention_metrics=attention_metrics,
                real_metrics_contract=real_metrics,
                performance_ingest=performance_ingest,
                publish_result=publish_result,
                reflection_memory=reflection_memory,
                probe_context=probe_context,
                resonance_engine=resonance_engine,
                reward_prediction=reward_prediction,
                thompson_sampler=thompson_sampler,
                decision_core_summary=decision_core_summary,
                evidence_interpreter=evidence_interpreter,
                experiment_resolution=experiment_resolution,
                recommendation_engine=recommendation_engine,
                wave10_summary=wave10_summary,
                wave11_summary=wave11_summary,
            )
            return (
                record,
                performance_ingest,
                attention_metrics,
                resonance_engine,
                reward_prediction,
                thompson_sampler,
                decision_core_summary,
                evidence_interpreter,
                experiment_resolution,
                recommendation_engine,
                wave10_summary,
                wave11_summary,
                experiment_registry,
                episodic_performance_memory,
                reflection_memory,
                learning_loop,
                performance_summary,
                performance_store,
            )
        except Exception as exc:
            fallback = self._measurement_fallback(
                reason=f"measurement_core_runtime_error: {type(exc).__name__}: {exc}"
            )
            return (*fallback, {"ok": False, "error": f"measurement_core_runtime_error: {type(exc).__name__}: {exc}"})

    def run(
        self,
        *,
        trend: str,
        force_placeholder: bool = False,
        force_real_probe: bool = False,
        probe_state: str | None = None,
    ) -> dict:
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
            visual_template_obj = resolve_visual_template(plan_dict)
            visual_template_dict = visual_template_obj.to_dict()
        except Exception as exc:
            visual_template_obj = None
            visual_template_dict = {"error": f"visual_template_error: {type(exc).__name__}: {exc}"}

        try:
            if visual_identity is None or typography is None or visual_contract is None or visual_template_obj is None:
                raise RuntimeError("visual dependencies unavailable")
            perceptual_qa_obj = evaluate_perceptual_quality(
                plan=plan_dict,
                contract=visual_contract,
                template=visual_template_obj,
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
            env_flags=env_flags,
            request_flags=request_flags,
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

        if lab_probe_policy.get("probe_block_reason"):
            block_reasons.append(str(lab_probe_policy.get("probe_block_reason")))
        if brand_surface_policy.get("block_reason"):
            block_reasons.append(str(brand_surface_policy.get("block_reason")))

        render_path = None
        render_error = None
        publish_result: dict[str, Any] | None = None

        linkage_context = {
            "operational_state": operational_state,
            "brand_live_allowed": False,
            "probe": {},
            "brand_surface_policy": brand_surface_policy,
            "lab_probe_policy": lab_probe_policy,
        }

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
            should_render = bool(lab_probe_policy.get("probe_render_requested"))
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
                lab_probe_policy.get("probe_eligible")
                and brand_surface_policy.get("main_surface_allowed")
                and render_path
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
                    "publish_status": "not_published_surface_protected",
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

        probe_context = {
            "requested": bool(lab_probe_policy.get("probe_requested")),
            "requested_state": lab_probe_policy.get("probe_state_requested"),
            "effective_state": lab_probe_policy.get("probe_state_effective"),
            "eligible": bool(
                lab_probe_policy.get("probe_eligible")
                and brand_surface_policy.get("main_surface_allowed")
            ),
            "render_executed": bool(lab_probe_policy.get("probe_render_executed")),
            "publish_executed": bool(lab_probe_policy.get("probe_publish_executed")),
            "render_path": render_path,
            "allow_real_publish": bool(
                lab_probe_policy.get("probe_eligible")
                and brand_surface_policy.get("main_surface_allowed")
            ),
            "probe_block_reason": lab_probe_policy.get("probe_block_reason") or brand_surface_policy.get("block_reason"),
            "surface_mode": brand_surface_policy.get("surface_mode"),
            "brand_surface_policy": brand_surface_policy,
            "lab_probe_policy": lab_probe_policy,
        }

        (
            post_performance_contract,
            performance_ingest,
            attention_metrics,
            resonance_engine,
            reward_prediction,
            thompson_sampler,
            decision_core_summary,
            evidence_interpreter,
            experiment_resolution,
            recommendation_engine,
            wave10_summary,
            wave11_summary,
            experiment_registry,
            episodic_performance_memory,
            reflection_memory,
            learning_loop,
            performance_summary,
            performance_store,
        ) = self._run_measurement_core(
            trend=trend,
            operational_state=operational_state,
            brand_live_allowed=False,
            creative_plan=plan_dict,
            editorial_qa=editorial_qa,
            visual_qa=visual_qa,
            visual_template=visual_template_dict,
            rubric_engine=rubric_engine,
            publication_authorization_gate=publication_authorization_gate,
            publish_result=publish_result,
            probe_context=probe_context,
        )

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
            "post_performance_contract": post_performance_contract,
            "performance_ingest": performance_ingest,
            "real_metrics_contract": performance_ingest.get("real_metrics") if isinstance(performance_ingest, dict) else None,
            "attention_metrics": attention_metrics,
            "resonance_engine": resonance_engine,
            "reward_prediction": reward_prediction,
            "thompson_sampler": thompson_sampler,
            "decision_core_summary": decision_core_summary,
            "publish_receipt_bridge": post_performance_contract.get("publish_receipt_bridge"),
            "evidence_bridge": post_performance_contract.get("evidence_bridge"),
            "evidence_interpreter": evidence_interpreter,
            "experiment_resolution": experiment_resolution,
            "recommendation_engine": recommendation_engine,
            "recommendation_state": recommendation_engine.get("recommended_action") if isinstance(recommendation_engine, dict) else None,
            "resolution_state": experiment_resolution.get("resolution_state") if isinstance(experiment_resolution, dict) else None,
            "wave10_summary": wave10_summary,
            "wave11_summary": wave11_summary,
            "experiment_registry": experiment_registry,
            "episodic_performance_memory": episodic_performance_memory,
            "reflection_memory": reflection_memory,
            "learning_loop": learning_loop,
            "performance_summary": performance_summary,
            "performance_store": performance_store,
            "runtime": self.snapshot(),
            "publish_result": publish_result,
            "last_publish": self.publish.last_publish(),
        }
