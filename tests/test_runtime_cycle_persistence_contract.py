from __future__ import annotations

import unittest
from unittest.mock import patch

from ace_next.runtime_cycle_persistence import build_runtime_cycle_record, persist_runtime_cycle


class _DummyConfig:
    pass


class _DummyStore:
    def __init__(self, config) -> None:
        self.config = config
        self.upsert_calls = []
        self.list_calls = []

    def upsert_record(self, record: dict) -> dict:
        self.upsert_calls.append(record)
        return {"ok": True, "record_id": record.get("record_id"), "stored": True}

    def list_records(self, limit: int = 0) -> list[dict]:
        self.list_calls.append(limit)
        return [{"record_id": "older-cycle"}]


class RuntimeCyclePersistenceContractTests(unittest.TestCase):
    def test_build_runtime_cycle_record_keeps_core_contract(self) -> None:
        runtime_result = {
            "trend": "clareza",
            "operational_state": "runtime_ready",
            "authorization_state": "authorized",
            "surface_mode": "official_runtime_surface",
            "publish_truth_state": "publish_truth_ready",
            "publish_result": {
                "publish_status": "published_real_probe",
                "receipt_id": "receipt-1",
                "probe": {
                    "requested": True,
                    "effective_state": "real_probe",
                },
            },
            "performance_ingest": {"real_metrics": {"saved": 3}},
            "attention_metrics": {"breakdown": {"attention_score": 8.4}},
            "recommendation_engine": {"recommended_action": "observe"},
            "experiment_resolution": {"resolution_state": "collecting"},
            "experiment_registry": {"active_variant": "hook_a"},
            "episodic_performance_memory": {"latest_episode": "ep-3"},
            "reflection_memory": {"guardrails": {"can_autopublish": False}},
            "creative_plan": {
                "goal": "retencao",
                "hypothesis": "hook com tensao",
                "hook": "pare agora",
                "headline": "clareza brutal",
                "publish_style": "editorial",
                "publish_format_now": "reel",
                "distribution_context": {"recommended_timing_hypothesis": "18h"},
                "serial_continuity": {"episode_role": "follow_up"},
            },
            "mission_decision": {
                "goal": "retencao",
                "hypothesis": "hook com tensao",
                "content_type": "reel",
                "style": "editorial",
                "confidence": 0.81,
            },
            "decision_memory_entries": [{"trend": "clareza"}],
            "decision_memory_summary": {"count": 1},
            "next_cycle_hook_candidate": "e se voce estiver errando o basico?",
        }

        record = build_runtime_cycle_record(runtime_result)

        self.assertEqual(record["record_id"], "receipt-1")
        self.assertEqual(record["trend"], "clareza")
        self.assertEqual(record["publish_status"], "published_real_probe")
        self.assertEqual(record["real_metrics"]["saved"], 3)
        self.assertEqual(record["attention_metrics"]["breakdown"]["attention_score"], 8.4)
        self.assertEqual(record["creative_plan"]["timing_hypothesis"], "18h")
        self.assertEqual(record["creative_plan"]["serial_continuity"]["episode_role"], "follow_up")
        self.assertTrue(record["probe_context"]["requested"])
        self.assertEqual(record["probe_context"]["effective_state"], "real_probe")
        self.assertFalse(record["reflection_memory"]["guardrails"]["can_autopublish"])
        self.assertEqual(record["next_cycle_hook_candidate"], "e se voce estiver errando o basico?")

    def test_persist_runtime_cycle_returns_error_when_runtime_result_is_empty(self) -> None:
        result = persist_runtime_cycle(_DummyConfig(), {})
        self.assertFalse(result["ok"])
        self.assertFalse(result["persisted"])
        self.assertEqual(result["error"], "runtime_result_empty")

    def test_persist_runtime_cycle_writes_record_and_builds_learning_summary(self) -> None:
        runtime_result = {
            "trend": "disciplina",
            "publish_result": {"publish_status": "scheduled", "receipt_id": "receipt-2"},
            "creative_plan": {"goal": "saves", "publish_format_now": "carousel"},
        }
        store = _DummyStore(_DummyConfig())

        with patch("ace_next.runtime_cycle_persistence.PerformanceStore", return_value=store), patch(
            "ace_next.runtime_cycle_persistence.build_learning_loop_summary",
            return_value={"ok": True, "planner_feedback_applied": True},
        ) as mocked_learning:
            result = persist_runtime_cycle(_DummyConfig(), runtime_result)

        self.assertTrue(result["ok"])
        self.assertTrue(result["persisted"])
        self.assertEqual(result["record_id"], "receipt-2")
        self.assertEqual(result["performance_store"]["record_id"], "receipt-2")
        self.assertTrue(result["learning_loop"]["planner_feedback_applied"])
        self.assertEqual(store.list_calls, [0])
        mocked_learning.assert_called_once()


if __name__ == "__main__":
    unittest.main()
