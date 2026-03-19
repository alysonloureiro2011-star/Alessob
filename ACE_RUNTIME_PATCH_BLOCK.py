# ==========================================================
# ACE Ω — RUNTIME OBSERVABILITY PATCH (SAFE ADDITIVE)
# NÃO REMOVE NADA EXISTENTE
# ==========================================================

import os
from datetime import datetime
from flask import jsonify

def _ace_runtime_meta():
    return {
        "runtime_release": os.getenv("ACE_RUNTIME_RELEASE", "unknown"),
        "runtime_commit": os.getenv("ACE_RUNTIME_COMMIT", "unknown"),
        "runtime_build": os.getenv("ACE_RUNTIME_BUILD", "unknown"),
    }

def _ace_publish_meta():
    try:
        if "last_publish_receipt" in globals():
            receipt = globals().get("last_publish_receipt")
        else:
            receipt = None

        if "last_publish_error" in globals():
            error = globals().get("last_publish_error")
        else:
            error = None

        return {
            "last_publish_receipt": receipt,
            "last_publish_error": error,
        }
    except Exception:
        return {
            "last_publish_receipt": None,
            "last_publish_error": None,
        }

@app.route("/health", methods=["GET"])
def ace_health():

    runtime = _ace_runtime_meta()
    publish = _ace_publish_meta()

    instagram_connected = False
    token_present = False
    ig_id_present = False

    try:
        if "INSTAGRAM_CONNECTED" in globals():
            instagram_connected = bool(globals().get("INSTAGRAM_CONNECTED"))

        if "IG_ACCESS_TOKEN" in os.environ:
            token_present = True

        if "IG_ID" in os.environ:
            ig_id_present = True

    except Exception:
        pass

    return jsonify({
        "ok": True,
        "app": "ACE Ω SUPREME",
        "online": True,
        "timestamp": datetime.utcnow().isoformat(),
        **runtime,
        **publish,
        "instagram_connected": instagram_connected,
        "token_present": token_present,
        "ig_id_present": ig_id_present,
        "real_publish_enabled": os.getenv("REAL_PUBLISH_ENABLED", "false"),
    })

try:
    original_status = app.view_functions.get("status")

    if original_status:

        def wrapped_status():
            base = original_status()
            try:
                if hasattr(base, "json"):
                    data = base.json
                else:
                    data = base.get_json()
            except Exception:
                return base

            runtime = _ace_runtime_meta()
            publish = _ace_publish_meta()

            data.update(runtime)
            data.update(publish)

            return jsonify(data)

        app.view_functions["status"] = wrapped_status

except Exception:
    pass

# ==========================================================
# FIM DO PATCH
# ==========================================================
