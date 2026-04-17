from __future__ import annotations

from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory

from .config import load_config
from .official_runtime_surface import OfficialRuntimeSurface


def _json_safe(value: Any):
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]

    if hasattr(value, "to_dict"):
        try:
            parsed = value.to_dict()
            return _json_safe(parsed)
        except Exception:
            return str(value)

    if isinstance(value, type):
        return value.__name__

    return str(value)


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _query_bool(name: str, default: bool = False) -> bool:
    raw = str(request.args.get(name, "")).strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on", "y", "sim", "s"}


def _compact_result(data: dict[str, Any]) -> dict[str, Any]:
    data = dict(data or {})
    publication_authorization_gate = dict(data.get("publication_authorization_gate") or {})
    publish_result = dict(data.get("publish_result") or {})
    recommendation_engine = dict(data.get("recommendation_engine") or {})
    experiment_resolution = dict(data.get("experiment_resolution") or {})
    performance_ingest = dict(data.get("performance_ingest") or {})
    real_metrics = dict(performance_ingest.get("real_metrics") or {})
    runtime = dict(data.get("runtime") or {})
    runtime_design = dict(runtime.get("runtime_design") or {})
    trend_guard = dict(data.get("trend_input_guard") or {})
    payload_resolution = dict(data.get("authorized_payload_resolution") or {})
    authorized_payload = dict(payload_resolution.get("authorized_payload") or {})
    reel_stack = dict(data.get("reel_stack") or {})
    publish_guard = dict(reel_stack.get("publish_guard") or {})
    release_authority = dict(reel_stack.get("release_authority") or {})
    quality_breakdown = dict(data.get("editorial_qa") or {})

    return {
        "ok": data.get("ok"),
        "mode": data.get("mode"),
        "authorization_state": data.get("authorization_state"),
        "operational_state": data.get("operational_state"),
        "trend": data.get("trend"),
        "trend_input_guard": {
            "changed": trend_guard.get("changed"),
            "warnings": trend_guard.get("warnings"),
            "confidence": trend_guard.get("confidence"),
            "sanitized_trend": trend_guard.get("sanitized_trend"),
        },
        "runtime_design": {
            "mode": runtime_design.get("mode"),
            "trend_input_guard": runtime_design.get("trend_input_guard"),
            "authorized_payload_resolver": runtime_design.get("authorized_payload_resolver"),
            "super_orchestrator_compatible": runtime_design.get("super_orchestrator_compatible"),
        },
        "quality": {
            "premium_classification": publication_authorization_gate.get("premium_classification"),
            "eligible_for_editorial_staging": publication_authorization_gate.get("eligible_for_editorial_staging"),
            "eligible_for_brand_live_candidate": publication_authorization_gate.get("eligible_for_brand_live_candidate"),
            "missing_for_brand_live": publication_authorization_gate.get("missing_for_brand_live"),
            "score_gap_to_brand_live": publication_authorization_gate.get("score_gap_to_brand_live"),
            "next_quality_lift_targets": publication_authorization_gate.get("next_quality_lift_targets"),
            "editorial_flags": quality_breakdown.get("flags"),
            "editorial_reasons": quality_breakdown.get("reasons"),
        },
        "authorized_payload": {
            "authorized_source": payload_resolution.get("authorized_source"),
            "changed_fields": payload_resolution.get("changed_fields"),
            "headline": authorized_payload.get("headline"),
            "hook": authorized_payload.get("hook"),
            "body": authorized_payload.get("body"),
            "cta": authorized_payload.get("cta"),
            "format": authorized_payload.get("format"),
        },
        "reel_gate": {
            "publish_guard_mode": publish_guard.get("mode"),
            "can_publish": publish_guard.get("can_publish"),
            "publish_guard_state": publish_guard.get("state"),
            "release_state": release_authority.get("release_state"),
            "approved_for_publish": release_authority.get("approved_for_publish"),
        },
        "publish_truth": {
            "publish_truth_state": data.get("publish_truth_state"),
            "publish_status": publish_result.get("publish_status"),
            "receipt_id": publish_result.get("receipt_id"),
            "media_id": publish_result.get("media_id"),
            "permalink": publish_result.get("permalink"),
        },
        "measurement": {
            "ingest_attempted": performance_ingest.get("attempted"),
            "collection_success": performance_ingest.get("collection_success"),
            "source_status": performance_ingest.get("source_status"),
            "real_metrics": real_metrics,
            "resolution_state": experiment_resolution.get("resolution_state"),
            "recommended_action": recommendation_engine.get("recommended_action"),
            "next_best_step": recommendation_engine.get("next_best_step"),
        },
        "runtime_cycle_persistence": data.get("runtime_cycle_persistence"),
        "performance_store": data.get("performance_store"),
        "last_run_summary": runtime.get("last_run_summary") or data.get("last_run_summary"),
        "block_reasons": data.get("block_reasons"),
    }


def _is_empty_last_run_summary(summary: Any) -> bool:
    if not isinstance(summary, dict):
        return True
    return not bool(summary)


def _is_empty_quality(data: dict[str, Any]) -> bool:
    return (
        data.get("premium_classification") is None
        and data.get("eligible_for_editorial_staging") is None
        and data.get("eligible_for_brand_live_candidate") is None
        and data.get("missing_for_brand_live") is None
        and data.get("score_gap_to_brand_live") is None
        and data.get("next_quality_lift_targets") is None
    )


def _is_empty_last_publish(data: dict[str, Any]) -> bool:
    return (
        data.get("latest_media_id") is None
        and data.get("latest_permalink") is None
        and data.get("latest_evidence_state") is None
        and data.get("latest_resolution_state") is None
    )


def _build_cached_last_run_summary(cached: dict[str, Any]) -> dict[str, Any]:
    summary = dict(cached.get("last_run_summary") or {})
    if summary:
        return summary

    publication_authorization_gate = dict(cached.get("publication_authorization_gate") or {})
    trend_guard = dict(cached.get("trend_input_guard") or {})
    payload_resolution = dict(cached.get("authorized_payload_resolution") or {})
    runtime_cycle_persistence = dict(cached.get("runtime_cycle_persistence") or {})
    reflection_adapter_summary = dict(cached.get("reflection_adapter_summary") or {})

    return {
        "timestamp": cached.get("timestamp"),
        "premium_classification": publication_authorization_gate.get("premium_classification"),
        "eligible_for_editorial_staging": publication_authorization_gate.get("eligible_for_editorial_staging"),
        "eligible_for_brand_live_candidate": publication_authorization_gate.get("eligible_for_brand_live_candidate"),
        "missing_for_brand_live": publication_authorization_gate.get("missing_for_brand_live"),
        "score_gap_to_brand_live": publication_authorization_gate.get("score_gap_to_brand_live"),
        "next_quality_lift_targets": publication_authorization_gate.get("next_quality_lift_targets"),
        "trend_input_guard": trend_guard,
        "authorized_payload_resolution": payload_resolution,
        "runtime_cycle_persistence": runtime_cycle_persistence,
        "reflection_adapter_state": reflection_adapter_summary.get("state"),
    }


def _build_cached_quality(cached: dict[str, Any]) -> dict[str, Any]:
    gate = dict(cached.get("publication_authorization_gate") or {})
    summary = _build_cached_last_run_summary(cached)

    return {
        "ok": True,
        "premium_classification": gate.get("premium_classification", summary.get("premium_classification")),
        "eligible_for_editorial_staging": gate.get(
            "eligible_for_editorial_staging",
            summary.get("eligible_for_editorial_staging"),
        ),
        "eligible_for_brand_live_candidate": gate.get(
            "eligible_for_brand_live_candidate",
            summary.get("eligible_for_brand_live_candidate"),
        ),
        "missing_for_brand_live": gate.get("missing_for_brand_live", summary.get("missing_for_brand_live")),
        "score_gap_to_brand_live": gate.get("score_gap_to_brand_live", summary.get("score_gap_to_brand_live")),
        "next_quality_lift_targets": gate.get(
            "next_quality_lift_targets",
            summary.get("next_quality_lift_targets"),
        ),
    }


def _build_cached_last_publish(cached: dict[str, Any]) -> dict[str, Any]:
    publish_result = dict(cached.get("publish_result") or {})
    evidence_bridge = dict(cached.get("evidence_bridge") or {})
    experiment_resolution = dict(cached.get("experiment_resolution") or {})

    return {
        "ok": True,
        "source_of_truth": "runtime_cache",
        "latest_media_id": publish_result.get("media_id"),
        "latest_permalink": publish_result.get("permalink"),
        "latest_evidence_state": evidence_bridge.get("bridge_state") or evidence_bridge.get("evidence_bridge_state"),
        "latest_resolution_state": experiment_resolution.get("resolution_state"),
        "updated_at": publish_result.get("created_at") or cached.get("timestamp"),
    }


def create_official_app() -> Flask:
    app = Flask(__name__)

    config = load_config()
    runtime_surface = OfficialRuntimeSurface(config)
    cache: dict[str, Any] = {"last_cycle_result": None}

    def _remember_cycle_result(result: dict[str, Any]) -> None:
        if isinstance(result, dict) and result:
            cache["last_cycle_result"] = result

    def safe_call(fn, fallback_name):
        try:
            return jsonify(_json_safe(fn()))
        except Exception as e:
            return jsonify(
                {
                    "ok": False,
                    "error": str(e),
                    "fallback": True,
                    "source": fallback_name,
                }
            )

    def safe_simple(data):
        try:
            return jsonify(_json_safe(data))
        except Exception as e:
            return jsonify(
                {
                    "ok": False,
                    "error": str(e),
                    "fallback": True,
                }
            )

    def build_feedback(data: dict) -> dict:
        return {
            "real_metrics": data.get("real_metrics"),
            "attention_metrics": data.get("attention_metrics"),
            "performance_ingest": data.get("performance_ingest"),
            "recommendation_engine": data.get("recommendation_engine"),
            "experiment_resolution": data.get("experiment_resolution"),
            "experiment_registry": data.get("experiment_registry"),
            "episodic_performance_memory": data.get("episodic_performance_memory"),
            "reflection_memory": data.get("reflection_memory"),
            "next_cycle_hook_candidate": data.get("next_cycle_hook_candidate"),
        }

    def run_cycle(
        *,
        trend: str,
        force_placeholder: bool,
        force_real_probe: bool,
        probe_state: str | None,
        feedback_payload: dict[str, Any] | None = None,
        compact: bool = False,
    ):
        result = runtime_surface.run(
            trend=trend,
            force_placeholder=force_placeholder,
            force_real_probe=force_real_probe,
            probe_state=probe_state,
            feedback_payload=feedback_payload,
        )
        _remember_cycle_result(result)
        if compact:
            return safe_simple(_compact_result(result))
        return safe_simple(result)

    @app.route("/")
    def home():
        return jsonify(
            {
                "ok": True,
                "service": "ACE Ω Runtime Online",
                "routes": {
                    "health": "/health",
                    "snapshot": "/snapshot",
                    "compact_summary": "/compact-summary",
                    "quality": "/quality",
                    "last_publish": "/last_publish",
                    "probe": "/probe",
                    "run_post_only": "/run",
                    "test_placeholder": "/test-placeholder",
                    "test_probe": "/test-probe",
                },
            }
        )

    @app.route("/health")
    def health():
        return jsonify({"ok": True})

    @app.route("/media/<path:filename>")
    def media(filename: str):
        safe_name = Path(filename).name
        if not safe_name or safe_name != filename:
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": "invalid_media_path",
                    }
                ),
                400,
            )

        media_dir = config.media_dir
        target = media_dir / safe_name

        if not target.exists() or not target.is_file():
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": "media_not_found",
                        "filename": safe_name,
                    }
                ),
                404,
            )

        response = send_from_directory(media_dir, safe_name, as_attachment=False)
        response.headers["Cache-Control"] = "public, max-age=300"
        return response

    @app.route("/snapshot")
    def snapshot():
        data = runtime_surface.snapshot()
        cached = cache.get("last_cycle_result")
        if cached and _is_empty_last_run_summary(data.get("last_run_summary")):
            data = dict(data)
            data["last_run_summary"] = _build_cached_last_run_summary(cached)
        return safe_simple(data)

    @app.route("/compact-summary")
    def compact_summary():
        data = runtime_surface.compact_runtime_summary()
        cached = cache.get("last_cycle_result")
        if cached and _is_empty_last_run_summary(data.get("last_run_summary")):
            data = dict(data)
            data["last_run_summary"] = _build_cached_last_run_summary(cached)
        return safe_simple(data)

    @app.route("/quality")
    def quality():
        data = runtime_surface.quality_gap_summary()
        cached = cache.get("last_cycle_result")
        if cached and _is_empty_quality(data):
            data = _build_cached_quality(cached)
        return safe_simple(data)

    @app.route("/last_publish")
    def last_publish():
        data = runtime_surface.last_publish_compact_summary()
        cached = cache.get("last_cycle_result")
        if cached and _is_empty_last_publish(data):
            data = _build_cached_last_publish(cached)
        return safe_simple(data)

    @app.route("/probe")
    def probe():
        return safe_call(runtime_surface.probe_readiness_summary, "probe")

    @app.route("/run", methods=["POST"])
    def run():
        data = request.get_json(force=True) or {}

        try:
            result = runtime_surface.run(
                trend=data.get("trend", ""),
                force_placeholder=bool(data.get("force_placeholder", False)),
                force_real_probe=bool(data.get("force_real_probe", False)),
                probe_state=data.get("probe_state"),
                feedback_payload=build_feedback(data),
            )
            _remember_cycle_result(result)
            if bool(data.get("compact", False)):
                return safe_simple(_compact_result(result))
            return safe_simple(result)

        except Exception as e:
            return jsonify(
                {
                    "ok": False,
                    "error": str(e),
                    "fallback": True,
                    "source": "run",
                }
            )

    @app.route("/test-placeholder")
    def test_placeholder():
        trend = _clean_text(request.args.get("trend")) or "disciplina e clareza na vida real"
        probe_state = _clean_text(request.args.get("state")) or "internal_lab"
        compact = _query_bool("compact", True)

        return run_cycle(
            trend=trend,
            force_placeholder=True,
            force_real_probe=False,
            probe_state=probe_state,
            feedback_payload=None,
            compact=compact,
        )

    @app.route("/test-probe")
    def test_probe():
        arm = _query_bool("arm", False)
        trend = _clean_text(request.args.get("trend")) or "disciplina e clareza na vida real"
        probe_state = _clean_text(request.args.get("state")) or "internal_lab"
        compact = _query_bool("compact", True)

        if probe_state not in {"internal_lab", "editorial_staging"}:
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": "invalid_probe_state",
                        "allowed_probe_states": ["internal_lab", "editorial_staging"],
                    }
                ),
                400,
            )

        if not arm:
            return jsonify(
                {
                    "ok": False,
                    "error": "probe_not_armed",
                    "message": "Para evitar publish real acidental, use arm=1 no link.",
                    "example": f"/test-probe?trend={trend.replace(' ', '%20')}&state={probe_state}&arm=1&compact=1",
                }
            )

        return run_cycle(
            trend=trend,
            force_placeholder=False,
            force_real_probe=True,
            probe_state=probe_state,
            feedback_payload=None,
            compact=compact,
        )

    return app


app = create_official_app()
