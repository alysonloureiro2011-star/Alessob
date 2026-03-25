from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .episodic_serial_contract import build_episode_memory_contract


@dataclass
class EpisodicPerformanceMemorySummary:
    ok: bool
    path: str
    total_episodes: int
    latest_episode_id: str | None
    latest_real_metrics_status: str | None
    latest_media_id: str | None
    latest_permalink: str | None
    latest_evidence_state: str | None
    latest_resolution_state: str | None
    latest_recommendation_state: str | None
    latest_series_name: str | None
    latest_continuity_state: str | None
    memory_reuse_rate: float
    learning_validity_score: float
    episodes_with_real_metrics: int
    episodes_with_receipt: int
    episodes_with_media_id: int
    episodes_with_permalink: int
    continuity_confirmed_count: int
    continuity_hypothesis_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EpisodicPerformanceMemory:
    def __init__(self, config: Any) -> None:
        self.config = config
        self.path = Path(config.data_dir) / "ace_next_episodic_performance_memory.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _empty_payload(self) -> dict[str, Any]:
        return {"ok": True, "version": "measurement_core_v2", "episodes": []}

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
            payload.setdefault("version", "measurement_core_v2")
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
        payload["episodes"] = episodes[-400:]
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
            if str(item.get("real_metrics_status") or "") in {"collected", "partial_collected"}
        )
        with_receipt = sum(1 for item in episodes if bool(item.get("receipt_linked")))
        with_media_id = sum(1 for item in episodes if bool(item.get("has_media_id")))
        with_permalink = sum(1 for item in episodes if bool(item.get("has_permalink")))
        evidence_ready = sum(1 for item in episodes if bool(item.get("evidence_ready_for_resolution")))
        continuity_confirmed = sum(1 for item in episodes if str(item.get("continuity_state")) == "continuity_confirmed")
        continuity_hypothesis = sum(1 for item in episodes if str(item.get("continuity_state")) == "continuity_hypothesis")

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
        media_ratio = (with_media_id / len(episodes)) if episodes else 0.0
        permalink_ratio = (with_permalink / len(episodes)) if episodes else 0.0
        real_ratio = (with_real / len(episodes)) if episodes else 0.0
        evidence_ready_ratio = (evidence_ready / len(episodes)) if episodes else 0.0

        learning_validity_score = round(
            (
                (receipt_ratio * 0.22)
                + (media_ratio * 0.18)
                + (permalink_ratio * 0.10)
                + (real_ratio * 0.25)
                + (evidence_ready_ratio * 0.15)
                + ((continuity_confirmed / len(episodes)) * 0.10 if episodes else 0.0)
            )
            * 100.0,
            2,
        )

        return EpisodicPerformanceMemorySummary(
            ok=True,
            path=str(self.path),
            total_episodes=len(episodes),
            latest_episode_id=latest.get("episode_id"),
            latest_real_metrics_status=latest.get("real_metrics_status"),
            latest_media_id=latest.get("media_id"),
            latest_permalink=latest.get("permalink"),
            latest_evidence_state=latest.get("evidence_state"),
            latest_resolution_state=latest.get("resolution_state"),
            latest_recommendation_state=latest.get("recommendation_state"),
            latest_series_name=latest.get("series_name"),
            latest_continuity_state=latest.get("continuity_state"),
            memory_reuse_rate=memory_reuse_rate,
            learning_validity_score=learning_validity_score,
            episodes_with_real_metrics=with_real,
            episodes_with_receipt=with_receipt,
            episodes_with_media_id=with_media_id,
            episodes_with_permalink=with_permalink,
            continuity_confirmed_count=continuity_confirmed,
            continuity_hypothesis_count=continuity_hypothesis,
        )


def build_episode_record(*, record: dict[str, Any]) -> dict[str, Any]:
    creative_plan = dict(record.get("creative_plan") or {})
    receipt = dict(record.get("receipt") or record.get("publish_result") or {})
    real_metrics = dict(record.get("real_metrics") or {})
    experiment_context = dict(record.get("experiment_registry") or {})
    visual_template = dict(record.get("visual_template") or {})
    evidence_bridge = dict(record.get("evidence_bridge") or {})
    evidence_interpreter = dict(record.get("evidence_interpreter") or {})
    experiment_resolution = dict(record.get("experiment_resolution") or {})
    recommendation_engine = dict(record.get("recommendation_engine") or {})
    serial_continuity = dict(
        creative_plan.get("serial_continuity")
        or record.get("serial_continuity")
        or {}
    )

    media_id = receipt.get("media_id")
    permalink = receipt.get("permalink")

    serial_contract = build_episode_memory_contract(
        record=record,
        serial_continuity=serial_continuity,
    )

    return {
        "episode_id": serial_contract.get("episode_id") or record.get("record_id"),
        "record_id": record.get("record_id"),
        "created_at": record.get("created_at"),
        "topic_seed": creative_plan.get("topic_seed"),
        "headline": creative_plan.get("headline"),
        "template_id": visual_template.get("template_id"),
        "operational_state": record.get("operational_state"),
        "receipt_linked": bool(receipt.get("receipt_id")),
        "receipt_id": receipt.get("receipt_id"),
        "publish_status": receipt.get("publish_status"),
        "has_real_receipt": bool(receipt.get("receipt_id")),
        "has_media_id": bool(media_id),
        "has_permalink": bool(permalink),
        "media_id": media_id,
        "permalink": permalink,
        "real_metrics_status": real_metrics.get("source_status"),
        "experiment_id": experiment_context.get("experiment_id"),
        "evidence_bridge_state": evidence_bridge.get("evidence_bridge_state"),
        "bridge_state": evidence_interpreter.get("bridge_state"),
        "evidence_state": evidence_interpreter.get("evidence_state"),
        "evidence_ready_for_resolution": evidence_interpreter.get("evidence_ready_for_resolution"),
        "resolution_state": experiment_resolution.get("resolution_state"),
        "recommendation_state": recommendation_engine.get("recommended_action"),
        "series_name": serial_contract.get("series_name"),
        "episode_index_hint": serial_contract.get("episode_index_hint"),
        "previous_episode_id": serial_contract.get("previous_episode_id"),
        "parent_episode_id": serial_contract.get("parent_episode_id"),
        "linked_series_candidate": serial_contract.get("linked_series_candidate"),
        "sequel_candidate": serial_contract.get("sequel_candidate"),
        "next_episode_seed": serial_contract.get("next_episode_seed"),
        "carryover_problem": serial_contract.get("carryover_problem"),
        "carryover_hook": serial_contract.get("carryover_hook"),
        "carryover_payoff": serial_contract.get("carryover_payoff"),
        "continuity_state": serial_contract.get("continuity_state"),
        "continuity_confidence": serial_contract.get("continuity_confidence"),
        "continuity_reason": serial_contract.get("continuity_reason"),
        "continuity_source_mode": serial_contract.get("continuity_source_mode"),
    }
