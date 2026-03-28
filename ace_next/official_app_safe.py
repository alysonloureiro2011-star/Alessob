from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from flask import Flask, jsonify, request

from .config import load_config
from .official_runtime_surface import OfficialRuntimeSurface
from .performance_store import PerformanceStore


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


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
    performance_store = PerformanceStore(config)

    def _feedback_payload(data: dict) -> dict:
        return {
            "real_metrics": data.get("real_metrics"),
            "attention_metrics": data.get("attention_metrics"),
            "performance_ingest": data.get("performance_ingest"),
            "recommendation_engine": data.get("recommendation_engine"),
            "experiment_resolution": data.get("experiment_resolution"),
            "experiment_registry": data.get("experiment_registry"),
            "episodic_performance_memory": data.get("episodic_performance_memory"),
            "reflection_memory": data.get("reflection_memory"),
            "next_cycle_hook_candidate": data.get("next_cycle_hook_candidate"),
        }

    def _latest_record() -> dict[str, Any]:
        records = performance_store.list_records(limit=1)
        if not records:
            return {}
        return _safe_dict(records[-1])

    def _latest_receipt_from_store() -> dict[str, Any]:
        latest = _latest_record()
        receipt = _safe_dict(latest.get("receipt") or latest.get("publish_result"))
        return receipt

    def _safe_snapshot_payload() -> dict[str, Any]:
        try:
            raw = runtime_surface.snapshot()
            sanitized = _json_safe(raw)
            if isinstance(sanitized, dict):
                return sanitized
            return {"ok": False, "error": "snapshot_not_dict", "raw": sanitized}
        except Exception as exc:
            latest = _latest_record()
            return {
                "ok": False,
                "error": f"snapshot_runtime_error: {type(exc).__name__}: {exc}",
                "timestamp": _now_iso(),
                "token_present": bool(getattr(config, "ig_token", None)),
                "ig_id_present": bool(getattr(config, "ig_id", None)),
                "enable_real_publish": bool(getattr(config, "enable_real_publish", False)),
                "performance_store": _json_safe(performance_store.summary().to_dict()),
                "last_record_id": latest.get("record_id"),
                "last_operational_state": latest.get("operational_state"),
                "safe_mode": True,
            }

    def _safe_quality_payload() -> dict[str, Any]:
        runtime_quality = _safe_dict(runtime_surface.quality_gap_summary())
        latest = _latest_record()
        latest_summary = _safe_dict(_safe_dict(latest.get("reflection_memory")).get("quality_summary"))
        latest_quality = _safe_dict(latest.get("quality_summary"))

        merged = {
            "ok": True,
            "premium_classification": runtime_quality.get("premium_classification"),
            "eligible_for_editorial_staging": runtime_quality.get("eligible_for_editorial_staging"),
            "eligible_for_brand_live_candidate": runtime_quality.get("eligible_for_brand_live_candidate"),
            "missing_for_brand_live": runtime_quality.get("missing_for_brand_live"),
            "score_gap_to_brand_live": runtime_quality.get("score_gap_to_brand_live"),
            "next_quality_lift_targets": runtime_quality.get("next_quality_lift_targets"),
            "source": "runtime_last_run_summary",
            "record_id": latest.get("record_id"),
        }

        if all(merged.get(key) is None for key in (
            "premium_classification",
            "eligible_for_editorial_staging",
            "eligible_for_brand_live_candidate",
            "missing_for_brand_live",
            "score_gap_to_brand_live",
            "next_quality_lift_targets",
        )):
            fallback = latest_quality or latest_summary
            if fallback:
                merged.update({
                    "premium_classification": fallback.get("premium_classification"),
                    "eligible_for_editorial_staging": fallback.get("eligible_for_editorial_staging"),
                    "eligible_for_brand_live_candidate": fallback.get("eligible_for_brand_live_candidate"),
                    "missing_for_brand_live": fallback.get("missing_for_brand_live"),
                    "score_gap_to_brand_live": fallback.get("score_gap_to_brand_live"),
                    "next_quality_lift_targets": fallback.get("next_quality_lift_targets"),
                    "source": "performance_store_fallback",
                })

        if merged.get("missing_for_brand_live") is None:
            merged["missing_for_brand_live"] = []
        if merged.get("next_quality_lift_targets") is None:
            merged["next_quality_lift_targets"] = []

        return _json_safe(merged)

    def _safe_last_publish_payload() -> dict[str, Any]:
        runtime_last = _safe_dict(runtime_surface.last_publish_compact_summary())
        receipt = _latest_receipt_from_store()
        latest = _latest_record()
        evidence = _safe_dict(latest.get("evidence_interpreter"))
        resolution = _safe_dict(latest.get("experiment_resolution"))

        if runtime_last.get("source_of_truth") == "legacy_fallback" and not runtime_last.get("latest_media_id"):
            if receipt:
                return _json_safe({
                    "ok": True,
                    "source_of_truth": "performance_store_fallback",
                    "latest_media_id": receipt.get("media_id"),
                    "latest_permalink": receipt.get("permalink"),
                    "latest_evidence_state": evidence.get("evidence_state"),
                    "latest_resolution_state": resolution.get("resolution_state"),
                    "updated_at": latest.get("created_at"),
                    "record_id": latest.get("record_id"),
                    "publish_status": receipt.get("publish_status"),
                    "receipt_id": receipt.get("receipt_id"),
                })

        enriched = dict(runtime_last)
        enriched.setdefault("record_id", latest.get("record_id"))
        enriched.setdefault("publish_status", receipt.get("publish_status"))
        enriched.setdefault("receipt_id", receipt.get("receipt_id"))
        return _json_safe(enriched)

    @app.route("/")
    def home():
        return jsonify({"ok": True, "service": "ACE Ω Runtime Safe Online"})

    @app.route("/health")
    def health():
        return jsonify({"ok": True, "safe_surface": True})

    @app.route("/snapshot")
    def snapshot():
        return jsonify(_safe_snapshot_payload())

    @app.route("/run", methods=["POST"])
    def run():
        data = request.get_json(force=True) or {}
        result = runtime_surface.run(
            trend=data.get("trend", ""),
            force_placeholder=bool(data.get("force_placeholder", False)),
            force_real_probe=bool(data.get("force_real_probe", False)),
            probe_state=data.get("probe_state"),
            feedback_payload=_feedback_payload(data),
        )
        return jsonify(_json_safe(result))

    @app.route("/probe")
    def probe():
        return jsonify(_json_safe(runtime_surface.probe_readiness_summary()))

    @app.route("/quality")
    def quality():
        return jsonify(_safe_quality_payload())

    @app.route("/last_publish")
    def last_publish():
        return jsonify(_safe_last_publish_payload())

    return app


app = create_official_app_safe()
