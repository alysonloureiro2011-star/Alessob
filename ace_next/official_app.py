from __future__ import annotations

import os
from datetime import datetime

from flask import Flask, jsonify, request

from .auth_store import load_instagram_auth
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

    @app.route("/instagram/token", methods=["GET", "POST"])
    def instagram_token_callback() -> object:
        code = (request.values.get("code") or "").strip()
        redirect_uri = (request.values.get("redirect_uri") or config.instagram_redirect_uri).strip()
        if not code:
            return jsonify({"ok": False, "error": "code ausente", "redirect_uri": redirect_uri}), 400

        result = exchange_code_for_token_with_redirect(
            config,
            code=code,
            redirect_uri=redirect_uri,
        )
        runtime.sync_instagram_auth()
        status = 200 if result.get("ok") else 400
        return jsonify({
            **result,
            "route": "/instagram/token",
            "redirect_uri": redirect_uri,
            "runtime": runtime.snapshot(),
        }), status

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
        return jsonify({
            **result,
            "route": "/instagram/token/long_lived",
            "runtime": runtime.snapshot(),
        }), status

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
        return jsonify({
            **result,
            "route": "/token/upgrade",
            "runtime": runtime.snapshot(),
        }), status

    @app.get("/debug/token/status")
    def debug_token_status() -> object:
        runtime.sync_instagram_auth()
        return jsonify({
            "ok": True,
            "route": "/debug/token/status",
            "timestamp": datetime.now().isoformat(),
            "runtime": runtime.snapshot(),
            "auth": load_instagram_auth(config),
            "env": {
                "IG_TOKEN": bool(config.ig_token),
                "IG_ACCESS_TOKEN": bool(os.environ.get("IG_ACCESS_TOKEN")),
                "INSTAGRAM_TOKEN": bool(os.environ.get("INSTAGRAM_TOKEN")),
                "IG_USER_ID": config.ig_id,
            },
        })

    return app


app = create_official_app()
