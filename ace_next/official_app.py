from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request

from .auth_store import auth_path, load_instagram_auth, sync_instagram_token_sources
from .config import load_config
from .official_runtime import OfficialRuntime

def create_official_app() -> Flask:
    config = load_config()
    runtime = OfficialRuntime(config)
    app = Flask(__name__)

    @app.before_request
    def before():
        runtime.sync_instagram_auth()

    @app.get("/")
    def home():
        return jsonify({
            "ok": True,
            "timestamp": datetime.now().isoformat()
        })

    @app.get("/status")
    def status():
        return jsonify({
            "ok": True,
            "runtime": runtime.snapshot()
        })

    # 🔥 DEBUG TOKEN SOURCE
    @app.get("/debug/token/source")
    def debug_token_source():
        return jsonify({
            "env": {
                "IG_TOKEN": bool(os.environ.get("IG_TOKEN")),
                "IG_ACCESS_TOKEN": bool(os.environ.get("IG_ACCESS_TOKEN")),
                "INSTAGRAM_TOKEN": bool(os.environ.get("INSTAGRAM_TOKEN")),
            },
            "config": {
                "ig_token": bool(config.ig_token),
                "ig_id": config.ig_id,
            },
            "auth_file": load_instagram_auth(config)
        })

    # 🔥 RESET AUTH (SEM SHELL)
    @app.get("/debug/auth/reset")
    def reset_auth():
        confirm = request.args.get("confirm")
        if confirm != "ACE_RESET_AUTH_2026":
            return jsonify({"ok": False, "error": "confirm inválido"}), 400

        path = auth_path(config)

        try:
            if Path(path).exists():
                Path(path).unlink()
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

        return jsonify({
            "ok": True,
            "message": "auth resetado"
        })

    @app.get("/publish/test")
    def publish_test():
        return jsonify({
            "ok": True,
            "message": "rota funcionando",
            "timestamp": datetime.now().isoformat()
        })
        
    return app

app = create_official_app()



