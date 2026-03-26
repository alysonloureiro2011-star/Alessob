from __future__ import annotations

import os
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory

from .auth_store import auth_path, load_instagram_auth, reset_instagram_auth
from .config import load_config
from .llm_orchestrator import llm_orchestrator_status
from .mission_control import decide_mission
from .observability_views import (
    build_analytics_view,
    build_llm_debug_view,
    build_mission_debug_view,
    build_observability_bundle,
    build_perf_view,
)
from .token_upgrade import (
    exchange_code_for_token_with_redirect,
    exchange_instagram_long_lived_token,
    upgrade_token_via_facebook_exchange,
)


def _safe_float_param(name: str) -> float | None:
    raw = request.args.get(name)
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        raise ValueError(f"invalid_float_param:{name}")


def _safe_int_param(name: str, default: int = 0) -> int:
    raw = request.args.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        return int(float(raw))
    except (TypeError, ValueError):
        raise ValueError(f"invalid_int_param:{name}")


def _is_compact_request() -> bool:
    return str(request.args.get("compact", "0")).strip().lower() in {"1", "true", "yes", "on"}


def create_official_app() -> Flask:
    config = load_config()
    app = Flask(__name__)

    runtime_holder: dict[str, object] = {}

    def get_runtime():
        runtime = runtime_holder.get("runtime")
        if runtime is None:
            from .official_runtime_surface import OfficialRuntimeSurface
            runtime = OfficialRuntimeSurface(config)
            runtime_holder["runtime"] = runtime
        return runtime

    def _build_runtime_probe_payload(runtime, trend: str | None) -> dict:
        trend = (trend or "").strip()
        if not trend:
            return {
                "runtime": runtime.snapshot(),
                "last_publish": runtime.runtime.publish.last_publish() if hasattr(runtime, "runtime") else runtime.publish.last_publish(),
            }
        return runtime.run(
            trend=trend,
            force_placeholder=False,
            force_real_probe=False,
            probe_state="auto",
        )

    @app.before_request
    def before_request_sync_ig_token() -> None:
        if request.path == "/health":
            return
        runtime = runtime_holder.get("runtime")
        if runtime is not None:
            runtime.sync_instagram_auth()

    @app.get("/")
    def home() -> object:
        return jsonify(
            {
                "ok": True,
                "app": "ace_next",
                "timestamp": datetime.now().isoformat(),
            }
        )

    @app.get("/health")
    def health() -> object:
        return jsonify(
            {
                "ok": True,
                "app": "ace_next",
                "health_mode": "lightweight",
                "runtime_loaded": "runtime" in runtime_holder,
                "timestamp": datetime.now().isoformat(),
            }
        )

    @app.get("/status")
    def status() -> object:
        runtime = get_runtime()
        publish_service = runtime.runtime.publish if hasattr(runtime, "runtime") else runtime.publish
        return jsonify(
            {
                "ok": True,
                "runtime": runtime.snapshot(),
                "last_publish": publish_service.last_publish(),
            }
        )

    @app.get("/ext/runtime")
    def ext_runtime() -> object:
        runtime = get_runtime()
        if _is_compact_request():
            return jsonify(
                {
                    "ok": True,
                    "route": "/ext/runtime",
                    **runtime.compact_runtime_summary(),
                }
            )
        publish_service = runtime.runtime.publish if hasattr(runtime, "runtime") else runtime.publish
        return jsonify(
            {
                "ok": True,
                "route": "/ext/runtime",
                "runtime": runtime.snapshot(),
                "last_publish": publish_service.last_publish(),
            }
        )

    @app.get("/ext/probe/readiness")
    def ext_probe_readiness() -> object:
        runtime = get_runtime()
        return jsonify(
            {
                "ok": True,
                "route": "/ext/probe/readiness",
                **runtime.probe_readiness_summary(),
            }
        )

    @app.get("/ext/quality/gap")
    def ext_quality_gap() -> object:
        runtime = get_runtime()
        return jsonify(
            {
                "ok": True,
                "route": "/ext/quality/gap",
                **runtime.quality_gap_summary(),
            }
        )

    @app.get("/ext/instagram/status")
    def ext_instagram_status() -> object:
        runtime = get_runtime()
        sync = runtime.sync_instagram_auth()
        publish_service = runtime.runtime.publish if hasattr(runtime, "runtime") else runtime.publish
        return jsonify(
            {
                "ok": True,
                "route": "/ext/instagram/status",
                "token_present": sync.get("token_present"),
                "ig_id_present": sync.get("ig_id_present"),
                "token_source": sync.get("token_source"),
                "user_id_source": sync.get("user_id_source"),
                "auth_path": sync.get("auth_path"),
                "runtime": runtime.snapshot(),
                "last_publish": publish_service.last_publish(),
            }
        )

    @app.get("/ext/publish/last")
    def ext_publish_last() -> object:
        runtime = get_runtime()
        if _is_compact_request():
            return jsonify(
                {
                    "ok": True,
                    "route": "/ext/publish/last",
                    **runtime.last_publish_compact_summary(),
                }
            )
        publish_service = runtime.runtime.publish if hasattr(runtime, "runtime") else runtime.publish
        return jsonify(
            {
                "ok": True,
                "route": "/ext/publish/last",
                "last_publish": publish_service.last_publish(),
            }
        )

    @app.get("/mission/test")
    def mission_test() -> object:
        try:
            trend = (request.args.get("trend") or "teste real").strip()
            format_hint = (request.args.get("format_hint") or "").strip() or None
            recent_signal_score = _safe_float_param("recent_signal_score")
            active_jobs = _safe_int_param("active_jobs", default=0)
            pending_jobs = _safe_int_param("pending_jobs", default=0)

            queue_state = {
                "active_jobs": active_jobs,
                "pending_jobs": pending_jobs,
            }

            runtime = get_runtime()
            runtime_snapshot = runtime.snapshot()

            signal_context = {
                "source": "http_route",
                "route": "/mission/test",
            }

            brand_context = {
                "brand_surface_mode": runtime_snapshot.get("brand_surface_mode"),
                "brand_live_allowed": runtime_snapshot.get("brand_live_allowed"),
            }

            decision = decide_mission(
                trend,
                format_hint=format_hint,
                signal_context=signal_context,
                brand_context=brand_context,
                queue_state=queue_state,
                recent_signal_score=recent_signal_score,
            )

            return jsonify(
                {
                    "ok": True,
                    "route": "/mission/test",
                    "decision": decision,
                    "runtime": runtime_snapshot,
                }
            )
        except Exception as exc:
            return jsonify(
                {
                    "ok": False,
                    "route": "/mission/test",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            ), 400

    @app.get("/debug/mission")
    def debug_mission() -> object:
        try:
            runtime = get_runtime()
            trend = (request.args.get("trend") or "").strip() or None
            payload = _build_runtime_probe_payload(runtime, trend)
            view = build_mission_debug_view(payload)
            return jsonify(
                {
                    "ok": True,
                    "route": "/debug/mission",
                    "view": view,
                }
            )
        except Exception as exc:
            return jsonify(
                {
                    "ok": False,
                    "route": "/debug/mission",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            ), 400

    @app.get("/ext/perf")
    def ext_perf() -> object:
        try:
            runtime = get_runtime()
            trend = (request.args.get("trend") or "").strip() or None
            payload = _build_runtime_probe_payload(runtime, trend)
            view = build_perf_view(payload)
            return jsonify(
                {
                    "ok": True,
                    "route": "/ext/perf",
                    "view": view,
                }
            )
        except Exception as exc:
            return jsonify(
                {
                    "ok": False,
                    "route": "/ext/perf",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            ), 400

    @app.get("/debug/analytics")
    def debug_analytics() -> object:
        try:
            runtime = get_runtime()
            trend = (request.args.get("trend") or "").strip() or None
            payload = _build_runtime_probe_payload(runtime, trend)
            llm_status = llm_orchestrator_status()
            bundle = build_observability_bundle(payload, orchestrator_status=llm_status)
            analytics = build_analytics_view(payload)
            return jsonify(
                {
                    "ok": True,
                    "route": "/debug/analytics",
                    "analytics": analytics,
                    "bundle": bundle,
                }
            )
        except Exception as exc:
            return jsonify(
                {
                    "ok": False,
                    "route": "/debug/analytics",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            ), 400

    @app.get("/debug/llm/status")
    def debug_llm_status() -> object:
        try:
            status = llm_orchestrator_status()
            view = build_llm_debug_view(status)
            return jsonify(
                {
                    "ok": True,
                    "route": "/debug/llm/status",
                    "view": view,
                }
            )
        except Exception as exc:
            return jsonify(
                {
                    "ok": False,
                    "route": "/debug/llm/status",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            ), 400

    @app.get("/debug/token/source")
    def debug_token_source() -> object:
        runtime = get_runtime()
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
        runtime = get_runtime()
        force = str(request.args.get("force", "0")).strip().lower() in ("1", "true", "yes", "on")
        result = runtime.runtime.ensure_fresh_instagram_token(force=force) if hasattr(runtime, "runtime") else runtime.ensure_fresh_instagram_token(force=force)
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
        runtime = get_runtime()
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
        runtime = get_runtime()
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
        runtime = get_runtime()
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
        runtime = get_runtime()
        trend = (request.args.get("trend") or "teste real").strip()

        force_placeholder = (
            str(request.args.get("placeholder", "0")).strip().lower()
            in ("1", "true", "yes", "on")
        )

        raw_probe = request.args.get("probe")
        if raw_probe is None:
            raw_probe = request.args.get("real_probe", "0")
        force_real_probe = str(raw_probe).strip().lower() in ("1", "true", "yes", "on")

        probe_state = (request.args.get("state") or request.args.get("probe_state") or "auto").strip()

        result = runtime.run(
            trend=trend,
            force_placeholder=force_placeholder,
            force_real_probe=force_real_probe,
            probe_state=probe_state,
        )

        if _is_compact_request():
            publish_result = dict(result.get("publish_result") or {})
            evidence_interpreter = dict(result.get("evidence_interpreter") or {})
            experiment_resolution = dict(result.get("experiment_resolution") or {})
            recommendation_engine = dict(result.get("recommendation_engine") or {})
            performance_summary = dict(result.get("performance_summary") or {})
            publish_state = dict(performance_summary.get("publish_state") or {})
            plan = dict(result.get("creative_plan") or {})
            authz = dict(result.get("publication_authorization_gate") or {})

            return jsonify(
                {
                    "ok": True,
                    "route": "/publish/test",
                    "authorization_state": result.get("authorization_state"),
                    "operational_state": result.get("operational_state"),
                    "probe_requested": result.get("probe_requested"),
                    "probe_eligible": result.get("probe_eligible"),
                    "probe_publish_executed": result.get("probe_publish_executed"),
                    "probe_block_reason": result.get("probe_block_reason"),
                    "publish_status": publish_result.get("publish_status") or publish_state.get("publish_status"),
                    "receipt_id": publish_result.get("receipt_id") or publish_state.get("receipt_id"),
                    "media_id": publish_result.get("media_id") or publish_state.get("media_id"),
                    "permalink": publish_result.get("permalink") or publish_state.get("permalink"),
                    "latest_evidence_state": evidence_interpreter.get("evidence_state"),
                    "latest_resolution_state": experiment_resolution.get("resolution_state"),
                    "recommended_action": recommendation_engine.get("recommended_action"),
                    "next_best_step": recommendation_engine.get("next_best_step"),
                    "premium_classification": authz.get("premium_classification"),
                    "eligible_for_editorial_staging": authz.get("eligible_for_editorial_staging"),
                    "eligible_for_brand_live_candidate": authz.get("eligible_for_brand_live_candidate"),
                    "score_gap_to_brand_live": authz.get("score_gap_to_brand_live"),
                    "missing_for_brand_live": authz.get("missing_for_brand_live"),
                    "caption_gate_result": plan.get("caption_gate_result"),
                    "caption_gate_score": plan.get("caption_gate_score"),
                }
            )

        return jsonify(result)

    @app.get("/media/<path:filename>")
    def media_file(filename: str) -> object:
        return send_from_directory(str(config.media_dir), filename)

    return app


app = create_official_app()
