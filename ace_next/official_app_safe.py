from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from flask import Flask, jsonify, request

from .config import load_config
from .official_runtime_surface import OfficialRuntimeSurface
from .performance_store import PerformanceStore


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dict(value: Any) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    return str(value)


def create_official_app_safe() -> Flask:
    app = Flask(__name__)

    config = load_config()
    runtime_surface = OfficialRuntimeSurface(config)
    store = PerformanceStore(config)

    def _latest_record():
        records = store.list_records(limit=1)
        return records[-1] if records else {}

    def _snapshot():
        try:
            return _json_safe(runtime_surface.snapshot())
        except Exception as e:
            last = _latest_record()
            return {
                "ok": False,
                "error": str(e),
                "fallback": True,
                "last_record": last.get("record_id"),
                "timestamp": _now_iso(),
            }

    def _quality():
        base = _safe_dict(runtime_surface.quality_gap_summary())
        last = _latest_record()
        fallback = _safe_dict(last.get("quality_summary"))

        if all(v is None for v in base.values()):
            base = fallback

        return _json_safe(base)

    def _last_publish():
        base = _safe_dict(runtime_surface.last_publish_compact_summary())
        last = _latest_record()
        receipt = _safe_dict(last.get("receipt") or last.get("publish_result"))

        if base.get("source_of_truth") == "legacy_fallback" and receipt:
            return {
                "ok": True,
                "source_of_truth": "store",
                "media_id": receipt.get("media_id"),
                "permalink": receipt.get("permalink"),
                "status": receipt.get("publish_status"),
                "record_id": last.get("record_id"),
            }

        return _json_safe(base)

    @app.route("/")
    def home():
        return jsonify({"ok": True, "safe": True})

    @app.route("/snapshot")
    def snapshot():
        return jsonify(_snapshot())

    @app.route("/quality")
    def quality():
        return jsonify(_quality())

    @app.route("/last_publish")
    def last_publish():
        return jsonify(_last_publish())

    @app.route("/run", methods=["POST"])
    def run():
        data = request.get_json(force=True) or {}
        result = runtime_surface.run(
            trend=data.get("trend", ""),
            force_placeholder=bool(data.get("force_placeholder", False)),
            force_real_probe=bool(data.get("force_real_probe", False)),
            probe_state=data.get("probe_state"),
            feedback_payload=data,
        )
        return jsonify(_json_safe(result))

    return app


app = create_official_app_safe()
