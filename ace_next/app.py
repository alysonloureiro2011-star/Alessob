from __future__ import annotations

from datetime import datetime

from flask import Flask, jsonify, request

from .config import load_config
from .runtime import AceNextRuntime


def create_app() -> Flask:
    config = load_config()
    runtime = AceNextRuntime(config)
    app = Flask(__name__)

    @app.get("/")
    def home():
        return jsonify({
            "ok": True,
            "app": config.app_name,
            "mode": "clean_foundation",
            "timestamp": datetime.now().isoformat(),
        })

    @app.get("/health")
    def health():
        return jsonify({
            "ok": True,
            "app": config.app_name,
            "timestamp": datetime.now().isoformat(),
            "runtime": runtime.snapshot(),
        })

    @app.get("/status")
    def status():
        return jsonify({
            "ok": True,
            "app": config.app_name,
            "timestamp": datetime.now().isoformat(),
            "runtime": runtime.snapshot(),
            "last_publish_receipt": runtime.publish.get_last_receipt(),
            "last_publish_error": runtime.publish.get_last_error(),
        })

    @app.get("/ext/runtime")
    def ext_runtime():
        return jsonify({
            "ok": True,
            "runtime": runtime.snapshot(),
        })

    @app.get("/ext/publish/last")
    def ext_publish_last():
        return jsonify({
            "ok": True,
            "timestamp": datetime.now().isoformat(),
            "storage": "ace_data/ace_next_publish_receipt.json",
            "last_publish_receipt": runtime.publish.get_last_receipt(),
            "last_publish_error": runtime.publish.get_last_error(),
        })

    @app.get("/ext/test/publish")
    def ext_test_publish():
        trend = (request.args.get("trend") or "disciplina com inteligência").strip()
        result = runtime.generate_once(trend=trend)
        return jsonify(result)

    return app
