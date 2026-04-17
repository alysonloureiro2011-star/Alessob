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
        "last_run_summary": runtime.get("last_run_summary"),
        "block_reasons": data.get("block_reasons"),
    }


def create_official_app() -> Flask:
    app = Flask(__name__)

    config = load_config()
    runtime_surface = OfficialRuntimeSurface(config)

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
        return safe_call(runtime_surface.snapshot, "snapshot")

    @app.route("/compact-summary")
    def compact_summary():
        return safe_call(runtime_surface.compact_runtime_summary, "compact-summary")

    @app.route("/quality")
    def quality():
        return safe_call(runtime_surface.quality_gap_summary, "quality")

    @app.route("/last_publish")
    def last_publish():
        return safe_call(runtime_surface.last_publish_compact_summary, "last_publish")

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
