from __future__ import annotations

import os
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory

from .auth_store import auth_path, load_instagram_auth, reset_instagram_auth
from .config import load_config
from .official_runtime import OfficialRuntime
from .token_upgrade import (
    exchange_code_for_token_with_redirect,
    exchange_instagram_long_lived_token,
    upgrade_token_via_facebook_exchange,
)


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
                "last_publish": runtime.publish.last_publish(),
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
                    "ACE_RENDER_API_KEY": bool(os.environ.get("ACE_RENDER_API_KEY")),
                },
                "runtime": runtime.snapshot(),
            }
        )

    @app.get("/debug/token/refresh")
    def debug_token_refresh() -> object:
        force = str(request.args.get("force", "0")).strip().lower() in ("1", "true", "yes", "on")
        result = runtime.ensure_fresh_instagram_token(force=force)
        status = 200 if result.get("ok") else 400
        return jsonify(
            {
                "ok": result.get("ok"),
                "route": "/debug/token/refresh",
                "force": force,
                **result,
            }
        ), status

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

    @app.post("/instagram/token")
    @app.get("/instagram/token")
    def instagram_token_callback() -> object:
        code = (request.values.get("code") or "").strip()
        redirect_uri = (request.values.get("redirect_uri") or config.instagram_redirect_uri).strip()

        if not code:
            return jsonify(
                {
                    "ok": False,
                    "error": "code ausente",
                    "redirect_uri": redirect_uri,
                }
            ), 400

        result = exchange_code_for_token_with_redirect(
            config,
            code=code,
            redirect_uri=redirect_uri,
        )
        runtime.sync_instagram_auth()
        status = 200 if result.get("ok") else 400
        return jsonify(
            {
                **result,
                "route": "/instagram/token",
                "redirect_uri": redirect_uri,
                "runtime": runtime.snapshot(),
            }
        ), status

    @app.get("/instagram/token/long_lived")
    def instagram_token_long_lived() -> object:
        runtime.sync_instagram_auth()
        result = exchange_instagram_long_lived_token(
            config,
            current_token=config.ig_token or "",
            current_user_id=config.ig_id,
        )
        runtime.sync_instagram_auth()
        status = 200 if result.get("ok") else 400
        return jsonify(
            {
                **result,
                "route": "/instagram/token/long_lived",
                "runtime": runtime.snapshot(),
            }
        ), status

    @app.get("/token/upgrade")
    def token_upgrade() -> object:
        runtime.sync_instagram_auth()
        result = upgrade_token_via_facebook_exchange(
            config,
            short_token=config.ig_token or "",
            current_user_id=config.ig_id,
        )
        runtime.sync_instagram_auth()
        status = 200 if result.get("ok") else 400
        return jsonify(
            {
                **result,
                "route": "/token/upgrade",
                "runtime": runtime.snapshot(),
            }
        ), status

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

    @app.get("/media/<path:filename>")
    def media_file(filename: str) -> object:
        return send_from_directory(str(config.media_dir), filename)

    return app


app = create_official_app()
