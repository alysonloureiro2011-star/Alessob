from __future__ import annotations

import os
from datetime import datetime

from flask import Flask, jsonify, request

from .auth_store import auth_path, load_instagram_auth, reset_instagram_auth
from .config import load_config
from .official_runtime import OfficialRuntime


def create_official_app() -> Flask:
    config = load_config()
    runtime = OfficialRuntime(config)
    app = Flask(__name__)

    @app.before_request
    def before_request_sync_ig_token() -> None:
        runtime.sync_instagram_auth()

    @app.get("/")
    def home() -> object:
        return jsonify(
            {
                "ok": True,
                "timestamp": datetime.now().isoformat(),
            }
        )

    @app.get("/health")
    def health() -> object:
        return jsonify(
            {
                "ok": True,
                "runtime": runtime.snapshot(),
            }
        )

    @app.get("/status")
    def status() -> object:
        return jsonify(
            {
                "ok": True,
                "runtime": runtime.snapshot(),
            }
        )

    @app.get("/debug/token/source")
    def debug_token_source() -> object:
        sync = runtime.sync_instagram_auth()
        return jsonify(
            {
                "ok": True,
                "token_present": sync.get("token_present"),
                "ig_id_present": sync.get("ig_id_present"),
                "token_source": sync.get("token_source"),
                "user_id_source": sync.get("user_id_source"),
                "auth_path": sync.get("auth_path"),
                "auth_file": load_instagram_auth(config),
                "config": {
                    "ig_token": bool(config.ig_token),
                    "ig_id": config.ig_id,
                },
                "env": {
                    "IG_TOKEN": bool(os.environ.get("IG_TOKEN")),
                    "IG_ACCESS_TOKEN": bool(os.environ.get("IG_ACCESS_TOKEN")),
                    "INSTAGRAM_TOKEN": bool(os.environ.get("INSTAGRAM_TOKEN")),
                    "IG_ID": os.environ.get("IG_ID"),
                    "IG_USER_ID": os.environ.get("IG_USER_ID"),
                },
                "runtime": runtime.snapshot(),
            }
        )

    @app.get("/debug/auth/reset")
    def debug_auth_reset() -> object:
        confirm = (request.args.get("confirm") or "").strip()
        if confirm != "ACE_RESET_AUTH_2026":
            return jsonify(
                {
                    "ok": False,
                    "error": "confirm inválido",
                    "auth_path": str(auth_path(config)),
                }
            ), 400

        result = reset_instagram_auth(config)
        return jsonify(result)

    @app.get("/publish/test")
    def publish_test() -> object:
        trend = (request.args.get("trend") or "teste real").strip()
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
