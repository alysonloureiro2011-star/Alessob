import os
import sys
from datetime import datetime
from flask import jsonify, request


def _truthy(value):
    return str(value or "").strip().lower() in ("1", "true", "yes", "on")


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
            "last_episode": summary.get("last_episode"),
        }
    except Exception:
        return {
            "last_publish_receipt": None,
            "last_publish_error": None,
            "last_episode": None,
        }


def _safe_log(level, event, detail=""):
    ace_bot_mod = sys.modules.get("ace_bot")
    log_fn = getattr(ace_bot_mod, "log", None)
    if callable(log_fn):
        try:
            log_fn(level, event, detail)
        except Exception:
            pass


def _legacy_readiness():
    ace_bot_mod = sys.modules.get("ace_bot")

    token = None
    ig_id = None
    real_publish_enabled = os.getenv("ACE_ENABLE_REAL_PUBLISH")

    if ace_bot_mod is not None:
        try:
            get_ig_token = getattr(ace_bot_mod, "get_ig_token", None)
            if callable(get_ig_token):
                token = get_ig_token()
        except Exception:
            token = None

        try:
            get_ig_id = getattr(ace_bot_mod, "get_ig_id", None)
            if callable(get_ig_id):
                ig_id = get_ig_id()
        except Exception:
            ig_id = None

        try:
            if real_publish_enabled is None and hasattr(ace_bot_mod, "ACE_ENABLE_REAL_PUBLISH"):
                real_publish_enabled = getattr(ace_bot_mod, "ACE_ENABLE_REAL_PUBLISH")
        except Exception:
            pass

    return {
        "instagram_connected": bool(token and ig_id),
        "token_present": bool(token),
        "ig_id_present": bool(ig_id),
        "real_publish_enabled": bool(
            real_publish_enabled
            if isinstance(real_publish_enabled, bool)
            else _truthy(real_publish_enabled)
        ),
    }


def _coerce_json_payload(response):
    primary = response[0] if isinstance(response, tuple) and response else response

    if isinstance(primary, dict):
        return dict(primary)

    get_json = getattr(primary, "get_json", None)
    if callable(get_json):
        try:
            payload = get_json(silent=True)
        except TypeError:
            try:
                payload = get_json()
            except Exception:
                payload = None
        except Exception:
            payload = None

        if isinstance(payload, dict):
            return dict(payload)

    return None


def _derive_bridge_state_from_receipt(receipt):
    receipt = dict(receipt or {})
    has_receipt = bool(receipt.get("receipt_id"))
    has_media_id = bool(receipt.get("media_id"))
    has_permalink = bool(receipt.get("permalink"))

    if has_receipt and has_media_id and has_permalink:
        return "receipt_with_permalink"
    if has_receipt and has_media_id:
        return "receipt_with_media_id"
    if has_receipt:
        return "receipt_linked"
    return "no_receipt"


def _derive_evidence_state_from_receipt(receipt):
    receipt = dict(receipt or {})
    has_receipt = bool(receipt.get("receipt_id"))
    has_media_id = bool(receipt.get("media_id"))

    if not has_receipt:
        return "no_receipt"
    if has_receipt and not has_media_id:
        return "receipt_only"
    return "linked_real_target"


def apply_runtime_patch(app):
    if app.config.get("ACE_RUNTIME_PATCH_V5_LOADED"):
        return

    app.config["ACE_RUNTIME_PATCH_V5_LOADED"] = True

    bridge_state = {
        "loaded": False,
        "runtime_available": False,
        "error": None,
        "routes": [
            "/",
            "/health",
            "/ext/runtime",
            "/ext/publish/last",
            "/ext/test/publish",
            "/ext/instagram/status",
            "/ext/evidence/last",
        ],
    }
    app.config["ACE_NEXT_BRIDGE_STATE"] = bridge_state

    runtime = None

    try:
        from ace_next.config import load_config
        from ace_next.official_runtime import OfficialRuntime

        runtime = OfficialRuntime(load_config())
        bridge_state["loaded"] = True
        bridge_state["runtime_available"] = True

        _safe_log(
            "INFO",
            "ace_next_official_bridge_loaded",
            {
                "runtime_available": True,
                "routes": bridge_state["routes"],
            },
        )
    except Exception as e:
        bridge_state["loaded"] = True
        bridge_state["runtime_available"] = False
        bridge_state["error"] = str(e)

        _safe_log(
            "WARN",
            "ace_next_official_bridge_import_failed",
            {
                "error": str(e),
                "fallback": True,
            },
        )

    def _runtime_snapshot():
        readiness = _legacy_readiness()

        if runtime is not None:
            try:
                payload = runtime.snapshot()
                if isinstance(payload, dict):
                    payload = dict(payload)
                    payload.setdefault("instagram_readiness", readiness)
                    payload["bridge"] = dict(bridge_state)
                    return payload
            except Exception as e:
                _safe_log(
                    "WARN",
                    "ace_next_official_bridge_snapshot_failed",
                    {
                        "error": str(e),
                        "fallback": True,
                    },
                )

                return {
                    "ok": False,
                    "runtime": "legacy_fallback",
                    "instagram_readiness": readiness,
                    "bridge": {
                        **dict(bridge_state),
                        "error": str(e),
                        "runtime_available": False,
                    },
                }

        return {
            "ok": False,
            "runtime": "legacy_fallback",
            "instagram_readiness": readiness,
            "bridge": dict(bridge_state),
        }

    def _last_publish_payload():
        if runtime is not None and hasattr(runtime, "publish"):
            try:
                payload = runtime.publish.last_publish()
                if isinstance(payload, dict):
                    return {
                        "last_publish_receipt": payload.get("last_publish_receipt"),
                        "last_publish_error": payload.get("last_publish_error"),
                        "last_episode": payload.get("last_episode"),
                    }
            except Exception as e:
                _safe_log(
                    "WARN",
                    "ace_next_official_bridge_last_publish_failed",
                    {
                        "error": str(e),
                        "fallback": True,
                    },
                )

        return _safe_publish_memory()

    def _bind_get_route(rule, endpoint, view_func):
        try:
            for existing_rule in app.url_map.iter_rules():
                if existing_rule.rule == rule and "GET" in existing_rule.methods:
                    app.view_functions[existing_rule.endpoint] = view_func
                    return existing_rule.endpoint
        except Exception:
            pass

        if endpoint in app.view_functions:
            app.view_functions[endpoint] = view_func
            return endpoint

        app.add_url_rule(
            rule,
            endpoint=endpoint,
            view_func=view_func,
            methods=["GET"],
        )
        return endpoint

    def home_view():
        readiness = _legacy_readiness()
        return jsonify(
            {
                "status": "ACE Ω SUPREME",
                "online": True,
                "timestamp": datetime.utcnow().isoformat(),
                "instagram_connected": readiness.get("instagram_connected", False),
            }
        )

    def health_view():
        readiness = _legacy_readiness()
        publish_payload = _last_publish_payload()

        data = {
            "ok": True,
            "app": "ACE Ω SUPREME",
            "online": True,
            "timestamp": datetime.utcnow().isoformat(),
            **_safe_runtime_meta(),
            **readiness,
            "bridge": dict(bridge_state),
            **publish_payload,
        }
        return jsonify(data)

    original_status = app.view_functions.get("status")
    if callable(original_status):

        def wrapped_status(*args, **kwargs):
            response = original_status(*args, **kwargs)
            payload = _coerce_json_payload(response)

            if isinstance(payload, dict):
                payload.update(_safe_runtime_meta())
                payload.update(_last_publish_payload())
                payload.update(_legacy_readiness())
                payload["bridge"] = dict(bridge_state)
                return jsonify(payload)

            return response

        app.view_functions["status"] = wrapped_status

    def ace_next_bridge_runtime_view():
        try:
            return jsonify(_runtime_snapshot())
        except Exception as e:
            return (
                jsonify(
                    {
                        "ok": False,
                        "route": "/ext/runtime",
                        "error": str(e),
                        "bridge": dict(bridge_state),
                    }
                ),
                500,
            )

    def ace_next_bridge_last_publish_view():
        try:
            payload = _last_publish_payload()
            return jsonify(
                {
                    "ok": True,
                    "route": "/ext/publish/last",
                    "last_publish_receipt": payload.get("last_publish_receipt"),
                    "last_publish_error": payload.get("last_publish_error"),
                    "last_episode": payload.get("last_episode"),
                    "bridge": dict(bridge_state),
                }
            )
        except Exception as e:
            return (
                jsonify(
                    {
                        "ok": False,
                        "route": "/ext/publish/last",
                        "error": str(e),
                        "bridge": dict(bridge_state),
                    }
                ),
                500,
            )

    def ace_next_bridge_instagram_status_view():
        try:
            runtime_snapshot = _runtime_snapshot()
            readiness = _legacy_readiness()
            return jsonify(
                {
                    "ok": True,
                    "route": "/ext/instagram/status",
                    "instagram_readiness": readiness,
                    "runtime": runtime_snapshot,
                    "bridge": dict(bridge_state),
                }
            )
        except Exception as e:
            return (
                jsonify(
                    {
                        "ok": False,
                        "route": "/ext/instagram/status",
                        "error": str(e),
                        "bridge": dict(bridge_state),
                    }
                ),
                500,
            )

    def ace_next_bridge_evidence_last_view():
        try:
            publish_payload = _last_publish_payload()
            receipt = dict(publish_payload.get("last_publish_receipt") or {})
            runtime_snapshot = _runtime_snapshot()
            performance_store = dict((runtime_snapshot.get("performance_store") or {})) if isinstance(runtime_snapshot, dict) else {}

            evidence_bridge_state = (
                performance_store.get("latest_evidence_bridge_state")
                or _derive_bridge_state_from_receipt(receipt)
            )
            evidence_state = _derive_evidence_state_from_receipt(receipt)

            return jsonify(
                {
                    "ok": True,
                    "route": "/ext/evidence/last",
                    "publish_status": receipt.get("publish_status"),
                    "receipt_id": receipt.get("receipt_id"),
                    "media_id": receipt.get("media_id"),
                    "permalink": receipt.get("permalink"),
                    "real_probe_requested": receipt.get("real_probe_requested"),
                    "real_probe_executed": receipt.get("real_probe_executed"),
                    "probe_state_requested": receipt.get("probe_state_requested"),
                    "probe_state_effective": receipt.get("probe_state_effective"),
                    "evidence_state": evidence_state,
                    "evidence_bridge_state": evidence_bridge_state,
                    "performance_store": performance_store,
                    "last_publish_error": publish_payload.get("last_publish_error"),
                    "bridge": dict(bridge_state),
                }
            )
        except Exception as e:
            return (
                jsonify(
                    {
                        "ok": False,
                        "route": "/ext/evidence/last",
                        "error": str(e),
                        "bridge": dict(bridge_state),
                    }
                ),
                500,
            )

    def ace_next_bridge_test_publish_view():
        trend = str(request.args.get("trend", "")).strip() or None
        live = _truthy(request.args.get("live"))
        placeholder = _truthy(request.args.get("placeholder"))

        raw_probe = request.args.get("probe")
        if raw_probe is None:
            raw_probe = request.args.get("real_probe")
        force_real_probe = _truthy(raw_probe)

        probe_state = str(
            request.args.get("state")
            or request.args.get("probe_state")
            or "auto"
        ).strip() or "auto"

        if not live:
            return jsonify(
                {
                    "ok": True,
                    "route": "/ext/test/publish",
                    "mode": "diagnostic",
                    "live_requested": False,
                    "trend": trend,
                    "placeholder_requested": placeholder,
                    "probe_requested": force_real_probe,
                    "probe_state": probe_state,
                    "next_live_example": (
                        "/ext/test/publish?live=1&probe=1&state=editorial_staging"
                        "&trend=probe_editorial_staging"
                    ),
                    "instagram_readiness": _legacy_readiness(),
                    "bridge": dict(bridge_state),
                }
            )

        if runtime is not None and hasattr(runtime, "run"):
            try:
                payload = runtime.run(
                    trend=trend or "teste real",
                    force_placeholder=placeholder,
                    force_real_probe=force_real_probe,
                    probe_state=probe_state,
                )
                if isinstance(payload, dict):
                    payload = dict(payload)
                    payload.setdefault("instagram_readiness", _legacy_readiness())
                    payload["bridge"] = dict(bridge_state)
                    payload["live_requested"] = True
                    payload["placeholder_requested"] = placeholder
                    payload["probe_requested_http"] = force_real_probe
                    payload["probe_state_http"] = probe_state
                    return jsonify(payload)
            except Exception as e:
                return (
                    jsonify(
                        {
                            "ok": False,
                            "route": "/ext/test/publish",
                            "error": str(e),
                            "trend": trend,
                            "live_requested": True,
                            "placeholder_requested": placeholder,
                            "probe_requested_http": force_real_probe,
                            "probe_state_http": probe_state,
                            "bridge": dict(bridge_state),
                        }
                    ),
                    500,
                )

        return jsonify(
            {
                "ok": False,
                "route": "/ext/test/publish",
                "mode": "bridge_fallback",
                "reason": "ace_next_runtime_unavailable",
                "trend": trend,
                "live_requested": True,
                "placeholder_requested": placeholder,
                "probe_requested_http": force_real_probe,
                "probe_state_http": probe_state,
                "instagram_readiness": _legacy_readiness(),
                "bridge": dict(bridge_state),
            }
        )

    _bind_get_route("/", "home", home_view)
    _bind_get_route("/health", "ace_runtime_patch_health_v5", health_view)
    _bind_get_route("/ext/runtime", "ace_ext_runtime_v1", ace_next_bridge_runtime_view)
    _bind_get_route("/ext/publish/last", "ace_last_publish_v1", ace_next_bridge_last_publish_view)
    _bind_get_route("/ext/test/publish", "ace_ext_test_publish_v2", ace_next_bridge_test_publish_view)
    _bind_get_route("/ext/instagram/status", "ace_ext_instagram_status_v1", ace_next_bridge_instagram_status_view)
    _bind_get_route("/ext/evidence/last", "ace_ext_evidence_last_v1", ace_next_bridge_evidence_last_view)

    _safe_log(
        "INFO",
        "ace_runtime_patch_v5_loaded",
        {
            "routes": bridge_state["routes"],
            "runtime_available": bridge_state["runtime_available"],
            "error": bridge_state["error"],
        },
    )
