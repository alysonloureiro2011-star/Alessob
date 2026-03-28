from __future__ import annotations

from flask import Flask, jsonify, request

from ace_next.config import load_config
from ace_next.official_runtime_surface import OfficialRuntimeSurface

app = Flask(__name__)

_surface: OfficialRuntimeSurface | None = None


def get_surface() -> OfficialRuntimeSurface:
    global _surface
    if _surface is None:
        config = load_config()
        _surface = OfficialRuntimeSurface(config)
    return _surface


def _feedback_payload(data: object) -> dict:
    if not isinstance(data, dict):
        return {}
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
def health():
    return {"ok": True, "service": "ACE Ω", "mode": "official_runtime_surface_bridge"}


@app.route("/ext/runtime")
def runtime_snapshot():
    surface = get_surface()
    return jsonify(surface.snapshot())


@app.route("/ext/run", methods=["GET", "POST"])
def run_pipeline():
    surface = get_surface()

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
    else:
        data = request.args

    trend = data.get("trend") or "tendência do dia"

    force_placeholder = str(data.get("force_placeholder", "0")).strip().lower() in {
        "1", "true", "yes", "on"
    }
    force_real_probe = str(data.get("force_real_probe", "0")).strip().lower() in {
        "1", "true", "yes", "on"
    }
    probe_state = data.get("probe_state") or "auto"

    feedback_payload = _feedback_payload(data) if request.method == "POST" else None

    result = surface.run(
        trend=trend,
        force_placeholder=force_placeholder,
        force_real_probe=force_real_probe,
        probe_state=probe_state,
        feedback_payload=feedback_payload,
    )
    return jsonify(result)


@app.route("/ext/test/publish", methods=["GET", "POST"])
def test_publish():
    surface = get_surface()

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
    else:
        data = request.args

    trend = data.get("trend") or "teste publicação"
    live = str(data.get("live", "0")).strip().lower()

    feedback_payload = _feedback_payload(data) if request.method == "POST" else None

    result = surface.run(
        trend=trend,
        force_real_probe=(live in {"1", "true", "yes", "on"}),
        force_placeholder=False,
        probe_state="auto",
        feedback_payload=feedback_payload,
    )

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
