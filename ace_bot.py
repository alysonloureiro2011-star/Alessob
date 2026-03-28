from __future__ import annotations

from flask import Flask, jsonify, request

from ace_next.config import AceNextConfig
from ace_next.official_runtime_surface import OfficialRuntimeSurface

app = Flask(__name__)

_surface: OfficialRuntimeSurface | None = None


def get_surface() -> OfficialRuntimeSurface:
    global _surface
    if _surface is None:
        config = AceNextConfig()
        _surface = OfficialRuntimeSurface(config)
    return _surface


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

    result = surface.run(
        trend=trend,
        force_placeholder=force_placeholder,
        force_real_probe=force_real_probe,
        probe_state=probe_state,
    )
    return jsonify(result)


@app.route("/ext/test/publish")
def test_publish():
    surface = get_surface()

    trend = request.args.get("trend") or "teste publicação"
    live = request.args.get("live", "0")

    result = surface.run(
        trend=trend,
        force_real_probe=(live == "1"),
        force_placeholder=False,
        probe_state="auto",
    )

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
