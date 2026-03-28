from flask import Flask, jsonify, request

from .config import AceNextConfig
from .official_runtime_surface import OfficialRuntimeSurface


def create_official_app() -> Flask:
    app = Flask(__name__)

    config = AceNextConfig()
    runtime_surface = OfficialRuntimeSurface(config)

    @app.route("/")
    def home():
        return jsonify({"ok": True, "service": "ACE Ω Runtime Online"})

    @app.route("/health")
    def health():
        return jsonify({"ok": True})

    @app.route("/snapshot")
    def snapshot():
        return jsonify(runtime_surface.snapshot())

    @app.route("/run", methods=["POST"])
    def run():
        data = request.get_json(force=True) or {}

        result = runtime_surface.run(
            trend=data.get("trend", ""),
            force_placeholder=bool(data.get("force_placeholder", False)),
            force_real_probe=bool(data.get("force_real_probe", False)),
            probe_state=data.get("probe_state"),
        )

        return jsonify(result)

    @app.route("/probe")
    def probe():
        return jsonify(runtime_surface.probe_readiness_summary())

    @app.route("/quality")
    def quality():
        return jsonify(runtime_surface.quality_gap_summary())

    @app.route("/last_publish")
    def last_publish():
        return jsonify(runtime_surface.last_publish_compact_summary())

    return app


app = create_official_app()
