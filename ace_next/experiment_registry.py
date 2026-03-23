from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class ExperimentRegistrySummary:
    ok: bool
    path: str
    total_experiments: int
    resolved_experiments: int
    experiments_resolved_percent: float
    latest_experiment_id: str | None
    latest_status: str | None
    winner_confidence: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExperimentRegistry:
    def __init__(self, config: Any) -> None:
        self.config = config
        self.path = Path(config.data_dir) / "ace_next_experiment_registry.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _empty_payload(self) -> dict[str, Any]:
        return {"ok": True, "version": "measurement_core_v1", "experiments": []}

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._empty_payload()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                return self._empty_payload()
            if not isinstance(payload.get("experiments"), list):
                payload["experiments"] = []
            payload.setdefault("ok", True)
            payload.setdefault("version", "measurement_core_v1")
            return payload
        except Exception:
            return self._empty_payload()

    def _save(self, payload: dict[str, Any]) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def upsert_experiment(self, record: dict[str, Any]) -> dict[str, Any]:
        payload = self._load()
        experiments = list(payload.get("experiments") or [])
        experiment_id = record.get("experiment_id")
        replaced = False
        if experiment_id:
            for index, existing in enumerate(experiments):
                if existing.get("experiment_id") == experiment_id:
                    experiments[index] = dict(record)
                    replaced = True
                    break
        if not replaced:
            experiments.append(dict(record))
        payload["experiments"] = experiments[-200:]
        self._save(payload)
        return self.summary().to_dict()

    def list_experiments(self, limit: int = 50) -> list[dict[str, Any]]:
        payload = self._load()
        experiments = list(payload.get("experiments") or [])
        if limit <= 0:
            return experiments
        return experiments[-limit:]

    def summary(self) -> ExperimentRegistrySummary:
        experiments = self.list_experiments(limit=0)
        total = len(experiments)
        resolved = sum(1 for item in experiments if item.get("status") == "resolved")
        latest = experiments[-1] if experiments else {}

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in experiments:
            grouped[str(item.get("hypothesis_key") or "unknown")].append(item)

        winner_confidence = None
        for _, items in grouped.items():
            resolved_items = [
                item
                for item in items
                if item.get("status") == "resolved" and item.get("attention_score") is not None
            ]
            if len(resolved_items) >= 2:
                ordered = sorted(
                    resolved_items,
                    key=lambda x: float(x.get("attention_score") or 0),
                    reverse=True,
                )
                top = float(ordered[0].get("attention_score") or 0)
                second = float(ordered[1].get("attention_score") or 0)
                if top > 0:
                    winner_confidence = round(max(0.0, min((top - second) / top * 100.0, 100.0)), 2)
                    break

        percent = round((resolved / total) * 100.0, 2) if total > 0 else 0.0
        return ExperimentRegistrySummary(
            ok=True,
            path=str(self.path),
            total_experiments=total,
            resolved_experiments=resolved,
            experiments_resolved_percent=percent,
            latest_experiment_id=latest.get("experiment_id"),
            latest_status=latest.get("status"),
            winner_confidence=winner_confidence,
        )


def _stable_id(*parts: str) -> str:
    base = "||".join(parts)
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]


def build_experiment_record(*, record: dict[str, Any]) -> dict[str, Any]:
    creative_plan = dict(record.get("creative_plan") or {})
    attention_metrics = dict(record.get("attention_metrics") or {})
    attention_breakdown = dict(attention_metrics.get("breakdown") or {})
    real_metrics = dict(record.get("real_metrics") or {})
    visual_template = dict(record.get("visual_template") or {})

    topic_seed = str(creative_plan.get("topic_seed") or creative_plan.get("trend_input") or "tema")
    template_id = str(visual_template.get("template_id") or creative_plan.get("visual_style") or "default")
    headline = str(creative_plan.get("headline") or "")
    hypothesis_key = _stable_id(topic_seed.lower(), template_id)
    variant_key = _stable_id(
        headline.lower(),
        template_id,
        str(record.get("operational_state") or ""),
    )
    experiment_id = f"exp_{hypothesis_key}_{variant_key[:8]}"

    source_status = str(real_metrics.get("source_status") or "not_available_yet")
    operational_state = str(record.get("operational_state") or "technical_test")

    if source_status == "collected" and attention_breakdown.get("attention_score") is not None:
        status = "resolved"
    elif source_status == "ingest_error":
        status = "ingest_error"
    elif operational_state in {"blocked_quality", "blocked_brand"}:
        status = "blocked"
    else:
        status = "collecting"

    decision = "observe"
    if status == "blocked":
        decision = "hold"
    elif status == "ingest_error":
        decision = "retry_ingestion"
    elif status == "resolved":
        decision = "review_manually"

    return {
        "experiment_id": experiment_id,
        "hypothesis_key": hypothesis_key,
        "hypothesis": f"A combinação editorial/visual de '{topic_seed}' pode elevar attention_score sem romper os gates soberanos.",
        "variant_key": variant_key,
        "variants": {
            "headline": headline,
            "hook": creative_plan.get("hook"),
            "template_id": template_id,
            "operational_state": operational_state,
        },
        "metric_target": "attention_score",
        "window": {
            "mode": "pending_real_metrics" if status == "collecting" else "closed_first_read",
        },
        "status": status,
        "decision": decision,
        "attention_score": attention_breakdown.get("attention_score"),
        "winner_confidence": None,
    }
