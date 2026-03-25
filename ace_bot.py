from __future__ import annotations

import datetime as _dt
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlencode

import requests
from flask import Flask, jsonify, redirect, request, send_from_directory

# ==========================================================
# ACE Ω — LEGACY SHELL CONTROLLED V3
# Bridge-first + fallback-only-if-missing
# Autoridade oficial:
# - ace_runtime_patch.py
# - ace_next/official_runtime.py
# ==========================================================

APP_NAME = "ACE Ω SUPREME"
PORT = int(os.getenv("PORT", "10000"))

RENDER_URL = (
    os.getenv("RENDER_EXTERNAL_URL", "").strip()
    or os.getenv("RENDER_URL", "").strip()
    or ""
)

AUTH_PATH = Path("instagram_auth.json")
MEDIA_DIR = Path(os.getenv("ACE_MEDIA_DIR", "ace_media"))

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "").strip()
INSTAGRAM_APP_ID = os.getenv("INSTAGRAM_APP_ID", "").strip()
INSTAGRAM_APP_SECRET = os.getenv("INSTAGRAM_APP_SECRET", "").strip()

ACE_OAUTH_DEFAULT_MODE = os.getenv("ACE_OAUTH_DEFAULT_MODE", "full").strip().lower()
ACE_OAUTH_FORCE_REAUTH = str(os.getenv("ACE_OAUTH_FORCE_REAUTH", "1")).strip().lower() in (
    "1",
    "true",
    "yes",
    "on",
)
ACE_ENABLE_WEBHOOK_OAUTH_BRIDGE = str(
    os.getenv("ACE_ENABLE_WEBHOOK_OAUTH_BRIDGE", "1")
).strip().lower() in ("1", "true", "yes", "on")

app = Flask(__name__)
sys.modules.setdefault("ace_bot", sys.modules[__name__])

IG_TOKEN_RUNTIME: str | None = None
IG_ID_RUNTIME: str | None = None

ACE_SHELL_STATE: dict[str, Any] = {
    "shell_mode": "legacy_shell_controlled_v3",
    "bridge_loaded": False,
    "bridge_error": None,
    "boot_at": _dt.datetime.now().isoformat(),
    "fallback_routes_registered": [],
}


# ==========================================================
# HELPERS BASE
# ==========================================================
def _truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in ("1", "true", "yes", "on")


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _route_error(route: str, err: Exception, status_code: int = 500):
    return (
        jsonify(
            {
                "ok": False,
                "route": route,
                "error": f"{err.__class__.__name__}: {err}",
                "timestamp": _dt.datetime.utcnow().isoformat(),
            }
        ),
        status_code,
    )


def _route_exists(path: str) -> bool:
    for rule in app.url_map.iter_rules():
        if rule.rule == path:
            return True
    return False


def _register_route_if_missing(
    path: str,
    endpoint: str,
    view_func: Callable[..., Any],
    methods: list[str] | tuple[str, ...] = ("GET",),
) -> None:
    if _route_exists(path):
        return
    app.add_url_rule(path, endpoint=endpoint, view_func=view_func, methods=list(methods))
    ACE_SHELL_STATE["fallback_routes_registered"].append(path)


# ==========================================================
# LOG
# ==========================================================
def log(level: str, event: str, detail: Any = "") -> None:
    stamp = _dt.datetime.now().isoformat()
    try:
        print(f"[{APP_NAME}][{level}] {stamp} | {event} | {detail}")
    except Exception:
        pass


# ==========================================================
# AUTH / TOKEN COMPAT
# ==========================================================
def get_ig_token() -> str | None:
    return (
        IG_TOKEN_RUNTIME
        or os.getenv("IG_TOKEN")
        or os.getenv("IG_ACCESS_TOKEN")
        or os.getenv("INSTAGRAM_TOKEN")
        or None
    )


def get_ig_id() -> str | None:
    value = IG_ID_RUNTIME or os.getenv("IG_USER_ID") or os.getenv("IG_ID") or None
    return _clean(value) if value else None


def save_instagram_auth(
    token: str | None = None,
    user_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    global IG_TOKEN_RUNTIME, IG_ID_RUNTIME

    payload = {
        "token": token or get_ig_token(),
        "user_id": user_id or get_ig_id(),
        "saved_at": _dt.datetime.now().isoformat(),
        "meta": meta or {},
    }

    try:
        AUTH_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as exc:
        log("WARN", "save_instagram_auth_fail", str(exc))

    if payload.get("token"):
        IG_TOKEN_RUNTIME = _clean(payload["token"])
    if payload.get("user_id"):
        IG_ID_RUNTIME = _clean(payload["user_id"])


def load_instagram_auth() -> None:
    global IG_TOKEN_RUNTIME, IG_ID_RUNTIME

    if not AUTH_PATH.exists():
        return

    try:
        data = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
        token = _clean(data.get("token"))
        user_id = _clean(data.get("user_id"))

        if token:
            IG_TOKEN_RUNTIME = token
        if user_id:
            IG_ID_RUNTIME = user_id
    except Exception as exc:
        log("WARN", "load_instagram_auth_fail", str(exc))


def ace_sync_ig_token_sources() -> dict[str, Any]:
    global IG_TOKEN_RUNTIME, IG_ID_RUNTIME

    unified_token = get_ig_token()
    unified_ig_id = get_ig_id()

    if unified_token:
        os.environ["IG_TOKEN"] = unified_token
        os.environ["IG_ACCESS_TOKEN"] = unified_token
        os.environ["INSTAGRAM_TOKEN"] = unified_token
        IG_TOKEN_RUNTIME = unified_token

    if unified_ig_id:
        os.environ["IG_USER_ID"] = unified_ig_id
        os.environ["IG_ID"] = unified_ig_id
        IG_ID_RUNTIME = unified_ig_id

    if unified_token or unified_ig_id:
        try:
            save_instagram_auth(
                token=unified_token,
                user_id=unified_ig_id,
                meta={"source": "legacy_shell_controlled_v3"},
            )
        except Exception:
            pass

    return {
        "token_present": bool(unified_token),
        "ig_id_present": bool(unified_ig_id),
        "instagram_connected": bool(unified_token and unified_ig_id),
        "ig_user_id": unified_ig_id,
    }


load_instagram_auth()
ace_sync_ig_token_sources()


@app.before_request
def ace_before_request_sync_ig_token() -> None:
    ace_sync_ig_token_sources()


# ==========================================================
# INSTAGRAM OAUTH HELPERS
# ==========================================================
def ace_ext_mode_scopes(mode: str = "basic") -> list[str]:
    mode = _clean(mode).lower() or "basic"
    if mode == "full":
        return [
            "instagram_business_basic",
            "instagram_business_content_publish",
            "instagram_business_manage_comments",
            "instagram_business_manage_messages",
            "instagram_business_manage_insights",
        ]
    return ["instagram_business_basic"]


def ace_ext_build_redirect_uri(target: str = "token") -> str:
    target = _clean(target).lower() or "token"
    if target == "webhook":
        return f"{RENDER_URL.rstrip('/')}/webhook" if RENDER_URL else "/webhook"
    return f"{RENDER_URL.rstrip('/')}/instagram/token" if RENDER_URL else "/instagram/token"


def build_instagram_oauth_url(mode: str | None = None, target: str = "token") -> str | None:
    if not INSTAGRAM_APP_ID:
        return None

    chosen_mode = _clean(mode).lower() or ACE_OAUTH_DEFAULT_MODE or "basic"
    scopes = ace_ext_mode_scopes(chosen_mode)
    redirect_uri = ace_ext_build_redirect_uri(target)

    params = {
        "client_id": INSTAGRAM_APP_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": ",".join(scopes),
    }

    if ACE_OAUTH_FORCE_REAUTH:
        params["force_reauth"] = "true"

    return f"https://www.instagram.com/oauth/authorize?{urlencode(params)}"


def ace_exchange_code_for_token_with_redirect(code: str, redirect_uri: str) -> dict[str, Any]:
    if not INSTAGRAM_APP_ID or not INSTAGRAM_APP_SECRET:
        return {
            "ok": False,
            "error": "INSTAGRAM_APP_ID ou INSTAGRAM_APP_SECRET ausentes",
        }

    data = {
        "client_id": INSTAGRAM_APP_ID,
        "client_secret": INSTAGRAM_APP_SECRET,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
        "code": code,
    }

    try:
        response = requests.post(
            "https://api.instagram.com/oauth/access_token",
            data=data,
            timeout=30,
        )
        try:
            body = response.json()
        except Exception:
            body = {"raw": response.text[:2000]}

        if response.status_code >= 400:
            log("WARN", "instagram_code_exchange_fail", body)
            return {"ok": False, "error": body, "status_code": response.status_code}

        access_token = _clean(body.get("access_token"))
        user_id = _clean(body.get("user_id"))

        if access_token:
            save_instagram_auth(
                token=access_token,
                user_id=user_id or get_ig_id(),
                meta={"source": "oauth_code_exchange", "redirect_uri": redirect_uri},
            )

        log("INFO", "instagram_code_exchange_ok", {"user_id": user_id})
        return {"ok": True, "data": body}
    except Exception as exc:
        log("WARN", "instagram_code_exchange_exception", str(exc))
        return {"ok": False, "error": str(exc)}


# ==========================================================
# STATUS PAYLOAD
# ==========================================================
def _runtime_meta() -> dict[str, Any]:
    return {
        "runtime_release": os.getenv("ACE_RUNTIME_RELEASE", "unknown"),
        "runtime_commit": os.getenv("ACE_RUNTIME_COMMIT", "unknown"),
        "runtime_build": os.getenv("ACE_RUNTIME_BUILD", "unknown"),
    }


def _compat_status_payload(route: str) -> dict[str, Any]:
    readiness = ace_sync_ig_token_sources()
    return {
        "ok": True,
        "route": route,
        "app": APP_NAME,
        "online": True,
        "timestamp": _dt.datetime.utcnow().isoformat(),
        "shell_mode": ACE_SHELL_STATE["shell_mode"],
        "bridge_loaded": ACE_SHELL_STATE["bridge_loaded"],
        "bridge_error": ACE_SHELL_STATE["bridge_error"],
        "oauth_default_mode": ACE_OAUTH_DEFAULT_MODE,
        "oauth_force_reauth": ACE_OAUTH_FORCE_REAUTH,
        "webhook_oauth_bridge": ACE_ENABLE_WEBHOOK_OAUTH_BRIDGE,
        "fallback_routes_registered": ACE_SHELL_STATE["fallback_routes_registered"],
        **_runtime_meta(),
        **readiness,
    }


# ==========================================================
# FALLBACK VIEW FUNCTIONS
# Registradas somente se a bridge NÃO tiver assumido a rota.
# ==========================================================
def home():
    return jsonify(
        {
            "status": APP_NAME,
            "online": True,
            "timestamp": _dt.datetime.utcnow().isoformat(),
            "instagram_connected": bool(get_ig_token() and get_ig_id()),
            "shell_mode": ACE_SHELL_STATE["shell_mode"],
            "bridge_loaded": ACE_SHELL_STATE["bridge_loaded"],
        }
    )


def health():
    return jsonify(_compat_status_payload("/health"))


def status():
    return jsonify(_compat_status_payload("/status"))


def serve_media(filename: str):
    return send_from_directory(str(MEDIA_DIR), filename)


def instagram_auth():
    try:
        url = build_instagram_oauth_url(mode=ACE_OAUTH_DEFAULT_MODE, target="token")
        if not url:
            return (
                jsonify(
                    {
                        "ok": False,
                        "route": "/instagram/auth",
                        "error": "instagram_oauth_url_indisponivel",
                    }
                ),
                400,
            )
        return redirect(url, code=302)
    except Exception as exc:
        return _route_error("/instagram/auth", exc)


def instagram_auth_url():
    try:
        mode = request.args.get("mode", ACE_OAUTH_DEFAULT_MODE)
        target = request.args.get("target", "token")
        url = build_instagram_oauth_url(mode=mode, target=target)
        return jsonify(
            {
                "ok": bool(url),
                "route": "/instagram/auth_url",
                "auth_url": url,
                "mode": mode,
                "target": target,
                "redirect_uri": ace_ext_build_redirect_uri(target),
                "scopes": ace_ext_mode_scopes(mode),
                "force_reauth": ACE_OAUTH_FORCE_REAUTH,
                "compat_mode": True,
            }
        )
    except Exception as exc:
        return _route_error("/instagram/auth_url", exc)


def instagram_token_callback():
    try:
        code = _clean(request.args.get("code"))
        error = request.args.get("error")
        error_reason = request.args.get("error_reason")
        error_description = request.args.get("error_description")

        if error:
            return (
                jsonify(
                    {
                        "ok": False,
                        "route": "/instagram/token",
                        "stage": "instagram_auth",
                        "error": error,
                        "error_reason": error_reason,
                        "error_description": error_description,
                    }
                ),
                400,
            )

        if not code:
            return jsonify(
                {
                    "ok": True,
                    "route": "/instagram/token",
                    "message": "Endpoint ativo. Use /instagram/auth para iniciar login.",
                    "redirect_uri_correto": ace_ext_build_redirect_uri("token"),
                    "token_present": bool(get_ig_token()),
                    "ig_id": get_ig_id(),
                    "compat_mode": True,
                }
            )

        result = ace_exchange_code_for_token_with_redirect(
            code=code,
            redirect_uri=ace_ext_build_redirect_uri("token"),
        )

        if result.get("ok"):
            return jsonify(
                {
                    "ok": True,
                    "route": "/instagram/token",
                    "message": "Token capturado com sucesso",
                    "user_id": get_ig_id(),
                    "token_present": bool(get_ig_token()),
                    "coloque_no_render": {
                        "IG_TOKEN": get_ig_token(),
                        "IG_ID": get_ig_id(),
                    },
                    "compat_mode": True,
                }
            )

        return (
            jsonify(
                {
                    "ok": False,
                    "route": "/instagram/token",
                    "message": "Falha ao trocar code por token",
                    "error": result.get("error"),
                }
            ),
            400,
        )
    except Exception as exc:
        return _route_error("/instagram/token", exc)


def webhook_gateway():
    try:
        if request.method == "GET" and request.args.get("code") and ACE_ENABLE_WEBHOOK_OAUTH_BRIDGE:
            code = _clean(request.args.get("code"))
            result = ace_exchange_code_for_token_with_redirect(
                code=code,
                redirect_uri=ace_ext_build_redirect_uri("webhook"),
            )

            if result.get("ok"):
                return jsonify(
                    {
                        "ok": True,
                        "route": "/webhook",
                        "message": "Token capturado com sucesso via webhook",
                        "user_id": get_ig_id(),
                        "token_present": bool(get_ig_token()),
                        "compat_mode": True,
                    }
                )

            return (
                jsonify(
                    {
                        "ok": False,
                        "route": "/webhook",
                        "message": "Falha ao trocar code por token via webhook",
                        "error": result.get("error"),
                    }
                ),
                400,
            )

        if request.method == "GET":
            verify_token = request.args.get("hub.verify_token", "")
            if VERIFY_TOKEN and verify_token == VERIFY_TOKEN:
                return request.args.get("hub.challenge", "OK")
            return "invalid verify token", 403

        payload = request.get_json(silent=True) or {}
        return (
            jsonify(
                {
                    "ok": True,
                    "route": "/webhook",
                    "compat_mode": True,
                    "message": "ACE_ACK",
                    "entry_count": len(payload.get("entry", []))
                    if isinstance(payload, dict)
                    else 0,
                }
            ),
            200,
        )
    except Exception as exc:
        return _route_error("/webhook", exc)


def ext_health():
    try:
        payload = _compat_status_payload("/ext/health")
        payload["compat_mode"] = True
        return jsonify(payload)
    except Exception as exc:
        return _route_error("/ext/health", exc)


def ext_runtime():
    try:
        return jsonify(
            {
                **_compat_status_payload("/ext/runtime"),
                "compat_mode": True,
                "message": "runtime_bridge_not_applied_yet_or_fallback_active",
            }
        )
    except Exception as exc:
        return _route_error("/ext/runtime", exc)


def ext_publish_last():
    try:
        return jsonify(
            {
                "ok": True,
                "route": "/ext/publish/last",
                "compat_mode": True,
                "last_publish_receipt": None,
                "last_publish_error": None,
                "last_episode": None,
                "bridge_loaded": ACE_SHELL_STATE["bridge_loaded"],
                "bridge_error": ACE_SHELL_STATE["bridge_error"],
            }
        )
    except Exception as exc:
        return _route_error("/ext/publish/last", exc)


def ext_test_publish():
    try:
        live = _truthy(request.args.get("live"))
        trend = _clean(request.args.get("trend")) or None

        return jsonify(
            {
                "ok": True,
                "route": "/ext/test/publish",
                "compat_mode": True,
                "mode": "diagnostic" if not live else "compat_live_blocked_here",
                "trend": trend,
                "live_requested": live,
                "message": "Esta rota deve ser assumida pela bridge oficial quando disponível.",
                "readiness": {
                    "instagram_connected": bool(get_ig_token() and get_ig_id()),
                    "token_present": bool(get_ig_token()),
                    "ig_id_present": bool(get_ig_id()),
                },
                "bridge_loaded": ACE_SHELL_STATE["bridge_loaded"],
                "bridge_error": ACE_SHELL_STATE["bridge_error"],
            }
        )
    except Exception as exc:
        return _route_error("/ext/test/publish", exc)


def ext_test_reel():
    try:
        return jsonify(
            {
                "ok": True,
                "route": "/ext/test/reel",
                "compat_mode": True,
                "message": "Wrapper fino temporário. Use a bridge/oficial runtime quando disponível.",
                "bridge_loaded": ACE_SHELL_STATE["bridge_loaded"],
                "bridge_error": ACE_SHELL_STATE["bridge_error"],
            }
        )
    except Exception as exc:
        return _route_error("/ext/test/reel", exc)


def ext_instagram_status():
    try:
        readiness = ace_sync_ig_token_sources()
        return jsonify(
            {
                "ok": True,
                "route": "/ext/instagram/status",
                "compat_mode": True,
                "instagram_connected": readiness["instagram_connected"],
                "token_present": readiness["token_present"],
                "ig_id_present": readiness["ig_id_present"],
                "ig_id": readiness["ig_user_id"],
                "oauth_default_mode": ACE_OAUTH_DEFAULT_MODE,
                "oauth_force_reauth": ACE_OAUTH_FORCE_REAUTH,
                "webhook_oauth_bridge": ACE_ENABLE_WEBHOOK_OAUTH_BRIDGE,
                "auth_url": build_instagram_oauth_url(
                    mode=ACE_OAUTH_DEFAULT_MODE,
                    target="token",
                ),
            }
        )
    except Exception as exc:
        return _route_error("/ext/instagram/status", exc)


# ==========================================================
# BRIDGE OFICIAL FIRST
# ==========================================================
def _apply_runtime_bridge() -> None:
    try:
        from ace_runtime_patch import apply_runtime_patch

        apply_runtime_patch(app)
        ACE_SHELL_STATE["bridge_loaded"] = True
        ACE_SHELL_STATE["bridge_error"] = None
        log("INFO", "ace_runtime_patch_loaded", {"ok": True})
    except Exception as exc:
        ACE_SHELL_STATE["bridge_loaded"] = False
        ACE_SHELL_STATE["bridge_error"] = str(exc)
        log("WARN", "ace_runtime_patch_load_fail", str(exc))


# ==========================================================
# FALLBACK REGISTRATION AFTER BRIDGE
# ==========================================================
def _register_fallback_routes() -> None:
    _register_route_if_missing("/", "home_fallback", home, ("GET",))
    _register_route_if_missing("/health", "health_fallback", health, ("GET",))
    _register_route_if_missing("/status", "status_fallback", status, ("GET",))
    _register_route_if_missing("/media/<path:filename>", "serve_media_fallback", serve_media, ("GET",))

    _register_route_if_missing("/instagram/auth", "instagram_auth_fallback", instagram_auth, ("GET",))
    _register_route_if_missing("/instagram/auth_url", "instagram_auth_url_fallback", instagram_auth_url, ("GET",))
    _register_route_if_missing("/instagram/token", "instagram_token_fallback", instagram_token_callback, ("GET",))
    _register_route_if_missing("/webhook", "webhook_fallback", webhook_gateway, ("GET", "POST"))

    _register_route_if_missing("/ext/health", "ext_health_fallback", ext_health, ("GET",))
    _register_route_if_missing("/ext/runtime", "ext_runtime_fallback", ext_runtime, ("GET",))
    _register_route_if_missing("/ext/publish/last", "ext_publish_last_fallback", ext_publish_last, ("GET",))
    _register_route_if_missing("/ext/test/publish", "ext_test_publish_fallback", ext_test_publish, ("GET",))
    _register_route_if_missing("/ext/test/reel", "ext_test_reel_fallback", ext_test_reel, ("GET",))
    _register_route_if_missing("/ext/instagram/status", "ext_instagram_status_fallback", ext_instagram_status, ("GET",))


_apply_runtime_bridge()
_register_fallback_routes()
log("INFO", "legacy_shell_controlled_v3_loaded", ACE_SHELL_STATE)


# ==========================================================
# MAIN
# ==========================================================
if __name__ == "__main__":
    log("INFO", "flask_start", {"port": PORT})
    app.run(host="0.0.0.0", port=PORT)
