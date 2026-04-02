from __future__ import annotations

from flask import Flask, jsonify, request

from .config import load_config
from .official_runtime_surface import OfficialRuntimeSurface


def _json_safe(value):
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


def create_official_app() -> Flask:
    app = Flask(__name__)

    config = load_config()
    runtime_surface = OfficialRuntimeSurface(config)

    def safe_call(fn, fallback_name):
        try:
            return jsonify(_json_safe(fn()))
        except Exception as e:
            return jsonify({
                "ok": False,
                "error": str(e),
                "fallback": True,
                "source": fallback_name,
            })

    def safe_simple(data):
        try:
            return jsonify(_json_safe(data))
        except Exception as e:
            return jsonify({
                "ok": False,
                "error": str(e),
                "fallback": True,
            })

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

    @app.route("/")
    def home():
        return jsonify({
            "ok": True,
            "service": "ACE Ω Runtime Online",
        })

    @app.route("/health")
    def health():
        return jsonify({"ok": True})

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
            return safe_simple(result)

        except Exception as e:
            return jsonify({
                "ok": False,
                "error": str(e),
                "fallback": True,
                "source": "run",
            })

    return app


app = create_official_app()
