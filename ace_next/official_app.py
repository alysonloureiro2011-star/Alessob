from __future__ import annotations

from datetime import datetime

from flask import Flask, jsonify, request

from .config import load_config
from .official_runtime import OfficialRuntime


def create_official_app() -> Flask:
    config = load_config()
    runtime = OfficialRuntime(config)
    app = Flask(__name__)

    @app.get("/")
    def home() -> object:
        return jsonify(
            {
                "ok": True,
                "app": config.app_name,
                "mode": "ace_next_official_core",
                "timestamp": datetime.now().isoformat(),
            }
        )

    @app.get("/health")
    def health() -> object:
        return jsonify(
            {
                "ok": True,
                "app": config.app_name,
                "timestamp": datetime.now().isoformat(),
                "runtime": runtime.snapshot(),
            }
        )

    @app.get("/status")
    def status() -> object:
        snapshot = runtime.snapshot()
        last_publish = runtime.publish.last_publish()
        return jsonify(
            {
                "ok": True,
                "app": config.app_name,
                "timestamp": datetime.now().isoformat(),
                "runtime": snapshot,
                "instagram_readiness": snapshot.get("instagram_readiness"),
                "memory": runtime.get_memory_summary(),
                "last_publish_receipt": last_publish.get("last_publish_receipt"),
                "last_publish_error": last_publish.get("last_publish_error"),
                "last_episode": last_publish.get("last_episode"),
            }
        )

    @app.get("/ext/runtime")
    def ext_runtime() -> object:
        snapshot = runtime.snapshot()
        return jsonify(
            {
                "ok": True,
                "runtime": snapshot,
                "instagram_readiness": snapshot.get("instagram_readiness"),
            }
        )

    @app.get("/ext/memory")
    def ext_memory() -> object:
        return jsonify(runtime.get_memory_summary())

    @app.get("/ext/publish/last")
    def ext_publish_last() -> object:
        last_publish = runtime.publish.last_publish()
        return jsonify(
            {
                "ok": True,
                "route": "/ext/publish/last",
                "timestamp": datetime.now().isoformat(),
                "last_publish_receipt": last_publish.get("last_publish_receipt"),
                "last_publish_error": last_publish.get("last_publish_error"),
                "last_episode": last_publish.get("last_episode"),
            }
        )

    @app.get("/ext/test/publish")
    def ext_test_publish() -> object:
        trend = (request.args.get("trend") or "disciplina com inteligência").strip()
        force_placeholder = (
            str(request.args.get("placeholder", "0")).strip().lower()
            in ("1", "true", "yes", "on")
        )
        result = runtime.run(
            trend=trend,
            force_placeholder=force_placeholder,
        )
        return jsonify(result)

    return app


app = create_official_app()
