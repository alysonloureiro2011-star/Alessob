from __future__ import annotations

import unittest

from ace_next.official_runtime_surface import OfficialRuntimeSurface


class _DummyConfig:
    pass


class OfficialRuntimeSurfaceFeedbackMergeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.surface = OfficialRuntimeSurface(_DummyConfig())

    def test_feedback_payload_normalizes_supported_sections(self) -> None:
        feedback = self.surface._feedback_payload(
            {
                "real_metrics": {"saved": 3},
                "attention_metrics": {"attention_score": 8.7},
                "performance_ingest": {"source": "graph_api"},
                "recommendation_engine": {"recommended_action": "promote"},
                "experiment_resolution": {"resolution_state": "winner"},
                "experiment_registry": {"active_variant": "hook_a"},
                "episodic_performance_memory": {"episode_role": "follow_up"},
                "reflection_memory": {"guardrails": {"can_autopublish": False}},
                "next_cycle_hook_candidate": "pare de perder alcance",
            }
        )

        self.assertEqual(feedback["real_metrics"], {"saved": 3})
        self.assertEqual(feedback["attention_metrics"], {"attention_score": 8.7})
        self.assertEqual(feedback["performance_ingest"], {"source": "graph_api"})
        self.assertEqual(feedback["recommendation_engine"]["recommended_action"], "promote")
        self.assertEqual(feedback["experiment_resolution"]["resolution_state"], "winner")
        self.assertEqual(feedback["experiment_registry"]["active_variant"], "hook_a")
        self.assertEqual(feedback["episodic_performance_memory"]["episode_role"], "follow_up")
        self.assertFalse(feedback["reflection_memory"]["guardrails"]["can_autopublish"])
        self.assertEqual(feedback["next_cycle_hook_candidate"], "pare de perder alcance")

    def test_merge_feedback_applies_real_metrics_and_runtime_learning_sections(self) -> None:
        result = {
            "performance_ingest": {"real_metrics": {"shares": 2}, "baseline": True},
            "real_metrics_contract": {"reach": 100},
            "attention_metrics": {"hold_rate": 0.42},
            "recommendation_engine": {"recommended_action": "observe"},
            "experiment_resolution": {"resolution_state": "collecting"},
            "experiment_registry": {"active_variant": "hook_b"},
            "episodic_performance_memory": {"episode_role": "setup"},
            "reflection_memory": {"guardrails": {"can_autopublish": True}},
        }

        merged = self.surface._merge_feedback(
            result,
            {
                "real_metrics": {"saved": 4},
                "attention_metrics": {"attention_score": 9.1},
                "performance_ingest": {"source": "manual_probe"},
                "recommendation_engine": {"recommended_action": "promote"},
                "experiment_resolution": {"resolution_state": "winner"},
                "experiment_registry": {"active_variant": "hook_c"},
                "episodic_performance_memory": {"episode_role": "payoff"},
                "reflection_memory": {"guardrails": {"can_autopublish": False}},
                "next_cycle_hook_candidate": "voce ainda nao viu o principal",
            },
        )

        self.assertEqual(merged["performance_ingest"]["real_metrics"], {"shares": 2, "saved": 4})
        self.assertEqual(merged["performance_ingest"]["source"], "manual_probe")
        self.assertTrue(merged["performance_ingest"]["baseline"])
        self.assertEqual(merged["real_metrics_contract"], {"reach": 100, "saved": 4})
        self.assertEqual(merged["attention_metrics"], {"hold_rate": 0.42, "attention_score": 9.1})
        self.assertEqual(merged["recommendation_engine"]["recommended_action"], "promote")
        self.assertEqual(merged["experiment_resolution"]["resolution_state"], "winner")
        self.assertEqual(merged["experiment_registry"]["active_variant"], "hook_c")
        self.assertEqual(merged["episodic_performance_memory"]["episode_role"], "payoff")
        self.assertFalse(merged["reflection_memory"]["guardrails"]["can_autopublish"])
        self.assertEqual(merged["next_cycle_hook_candidate"], "voce ainda nao viu o principal")

    def test_merge_feedback_ignores_invalid_payloads_and_preserves_result(self) -> None:
        result = {
            "performance_ingest": {"real_metrics": {"shares": 1}},
            "attention_metrics": {"hold_rate": 0.5},
        }

        merged = self.surface._merge_feedback(result, {"real_metrics": None, "attention_metrics": "bad"})

        self.assertEqual(merged["performance_ingest"]["real_metrics"], {"shares": 1})
        self.assertEqual(merged["attention_metrics"], {"hold_rate": 0.5})
        self.assertNotIn("next_cycle_hook_candidate", merged)


if __name__ == "__main__":
    unittest.main()
