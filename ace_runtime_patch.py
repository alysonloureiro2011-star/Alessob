import os
from datetime import datetime
from flask import jsonify


def _safe_runtime_meta():
    return {
        "runtime_release": os.getenv("ACE_RUNTIME_RELEASE", "unknown"),
        "runtime_commit": os.getenv("ACE_RUNTIME_COMMIT", "unknown"),
        "runtime_build": os.getenv("ACE_RUNTIME_BUILD", "unknown"),
    }


def _safe_publish_memory():
    try:
        from ace.engines.episodic_memory_engine import build_memory_summary
        summary = build_memory_summary() or {}
        return {
            "last_publish_receipt": summary.get("last_publish_receipt"),
            "last_publish_error": summary.get("last_publish_error"),
        }
    except Exception:
        return {
            "last_publish_receipt": None,
            "last_publish_error": None,
        }


def apply_runtime_patch(app):

    runtime_meta = _safe_runtime_meta()
    publish_meta = _safe_publish_memory()

    # ===============================
    # HEALTH ROUTE
    # ===============================
    @app.route("/health", methods=["GET"])
    def health():
        data = {
            "ok": True,
            "app": "ACE Ω SUPREME",
            "online": True,
            "timestamp": datetime.utcnow().isoformat(),
            **runtime_meta,
            **publish_meta,
        }
        return jsonify(data)

    # ===============================
    # STATUS ENHANCER
    # ===============================
    original_status = app.view_functions.get("status")

    if original_status:
        def wrapped_status(*args, **kwargs):
            response = original_status(*args, **kwargs)

            try:
                json_data = response.get_json()
                if isinstance(json_data, dict):
                    json_data.update(runtime_meta)
                    json_data.update(publish_meta)
                    return jsonify(json_data)
            except Exception:
                pass

            return response

        app.view_functions["status"] = wrapped_status
