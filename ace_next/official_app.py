from flask import Flask, jsonify, request

from .config import load_config
from .official_runtime_surface import OfficialRuntimeSurface


def create_official_app() -> Flask:
    app = Flask(__name__)

    config = load_config()
    runtime_surface = OfficialRuntimeSurface(config)

    def _safe_json(data):
        try:
            return jsonify(data)
        except Exception as e:
            return jsonify({
                "ok": False,
                "error": str(e),
                "fallback": True
            })

    def _feedback_payload(data: dict) -> dict:
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
        return jsonify({"ok": True, "service": "ACE Ω Runtime Online"})

    @app.route("/health")
    def health():
        return jsonify({"ok": True})

    @app.route("/snapshot")
    def snapshot():
        try:
            return _safe_json(runtime_surface.snapshot())
        except Exception as e:
            return jsonify({
                "ok": False,
                "error": str(e),
                "safe_mode": True
            })

    @app.route("/run", methods=["POST"])
    def run():
        data = request.get_json(force=True) or {}

        result = runtime_surface.run(
            trend=data.get("trend", ""),
            force_placeholder=bool(data.get("force_placeholder", False)),
            force_real_probe=bool(data.get("force_real_probe", False)),
            probe_state=data.get("probe_state"),
            feedback_payload=_feedback_payload(data),
        )

        return _safe_json(result)

    @app.route("/probe")
    def probe():
        return _safe_json(runtime_surface.probe_readiness_summary())

    @app.route("/quality")
    def quality():
        try:
            return _safe_json(runtime_surface.quality_gap_summary())
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)})

    @app.route("/last_publish")
    def last_publish():
        try:
            return _safe_json(runtime_surface.last_publish_compact_summary())
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)})

    return app


app = create_official_app()
