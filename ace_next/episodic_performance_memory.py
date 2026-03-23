from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class EpisodicPerformanceMemorySummary:
    ok: bool
    path: str
    total_episodes: int
    latest_episode_id: str | None
    latest_real_metrics_status: str | None
    memory_reuse_rate: float
    learning_validity_score: float
    episodes_with_real_metrics: int
    episodes_with_receipt: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EpisodicPerformanceMemory:
    def __init__(self, config: Any) -> None:
        self.config = config
        self.path = Path(config.data_dir) / "ace_next_episodic_performance_memory.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _empty_payload(self) -> dict[str, Any]:
        return {"ok": True, "version": "measurement_core_v1", "episodes": []}

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._empty_payload()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                return self._empty_payload()
            if not isinstance(payload.get("episodes"), list):
                payload["episodes"] = []
            payload.setdefault("ok", True)
            payload.setdefault("version", "measurement_core_v1")
            return payload
        except Exception:
            return self._empty_payload()

    def _save(self, payload: dict[str, Any]) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def upsert_episode(self, episode: dict[str, Any]) -> dict[str, Any]:
        payload = self._load()
        episodes = list(payload.get("episodes") or [])
        episode_id = episode.get("episode_id")
        replaced = False
        if episode_id:
            for index, existing in enumerate(episodes):
                if existing.get("episode_id") == episode_id:
                    episodes[index] = dict(episode)
                    replaced = True
                    break
        if not replaced:
            episodes.append(dict(episode))
        payload["episodes"] = episodes[-300:]
        self._save(payload)
        return self.summary().to_dict()

    def list_episodes(self, limit: int = 50) -> list[dict[str, Any]]:
        payload = self._load()
        episodes = list(payload.get("episodes") or [])
        if limit <= 0:
            return episodes
        return episodes[-limit:]

    def summary(self) -> EpisodicPerformanceMemorySummary:
        episodes = self.list_episodes(limit=0)
        latest = episodes[-1] if episodes else {}

        with_real = sum(
            1 for item in episodes
            if str(item.get("real_metrics_status") or "") == "collected"
        )
        with_receipt = sum(1 for item in episodes if bool(item.get("receipt_linked")))

        seen_pairs: set[tuple[str, str]] = set()
        reused = 0
        for item in episodes:
            pair = (str(item.get("topic_seed") or ""), str(item.get("template_id") or ""))
            if pair in seen_pairs:
                reused += 1
            else:
                seen_pairs.add(pair)

        memory_reuse_rate = round((reused / len(episodes)) * 100.0, 2) if episodes else 0.0

        receipt_ratio = (with_receipt / len(episodes)) if episodes else 0.0
        real_ratio = (with_real / len(episodes)) if episodes else 0.0
        learning_validity_score = round(((receipt_ratio * 0.5) + (real_ratio * 0.5)) * 100.0, 2)

        return EpisodicPerformanceMemorySummary(
            ok=True,
            path=str(self.path),
            total_episodes=len(episodes),
            latest_episode_id=latest.get("episode_id"),
            latest_real_metrics_status=latest.get("real_metrics_status"),
            memory_reuse_rate=memory_reuse_rate,
            learning_validity_score=learning_validity_score,
            episodes_with_real_metrics=with_real,
            episodes_with_receipt=with_receipt,
        )


def build_episode_record(*, record: dict[str, Any]) -> dict[str, Any]:
    creative_plan = dict(record.get("creative_plan") or {})
    receipt = dict(record.get("receipt") or record.get("publish_result") or {})
    real_metrics = dict(record.get("real_metrics") or {})
    experiment_context = dict(record.get("experiment_registry") or {})
    visual_template = dict(record.get("visual_template") or {})

    return {
        "episode_id": record.get("record_id"),
        "record_id": record.get("record_id"),
        "created_at": record.get("created_at"),
        "topic_seed": creative_plan.get("topic_seed"),
        "headline": creative_plan.get("headline"),
        "template_id": visual_template.get("template_id"),
        "operational_state": record.get("operational_state"),
        "receipt_linked": bool(receipt),
        "receipt_id": receipt.get("receipt_id"),
        "real_metrics_status": real_metrics.get("source_status"),
        "experiment_id": experiment_context.get("experiment_id"),
    }
