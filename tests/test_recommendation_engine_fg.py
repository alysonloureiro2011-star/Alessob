import unittest

from ace_next.recommendation_engine import build_recommendation_engine


class RecommendationEngineFGTest(unittest.TestCase):
    def test_repeat_probe_without_receipt(self):
        result = build_recommendation_engine(
            evidence_interpreter={"evidence_state": "no_receipt"},
            experiment_resolution={"resolution_state": "collecting"},
            resonance_engine={},
            reward_prediction={},
            attention_metrics={},
            operational_state="internal_lab",
        )
        self.assertEqual(result["recommended_action"], "repeat_probe")
        self.assertTrue(result["safe_to_repeat"])

    def test_memory_informed_series_action(self):
        result = build_recommendation_engine(
            evidence_interpreter={"evidence_state": "receipt_with_media_id"},
            experiment_resolution={"resolution_state": "observe"},
            resonance_engine={},
            reward_prediction={},
            attention_metrics={"breakdown": {"attention_score": 61}},
            operational_state="editorial_staging",
            episodic_memory={"episode_id": "ep_001"},
            serial_continuity={
                "linked_series_candidate": True,
                "continuity_state": "continuity_confirmed",
            },
            distribution_context={
                "recommended_next_format": "carousel",
                "recommended_next_angle": "aprofundar payoff concreto",
                "recommended_next_series_action": "continuar série",
                "recommended_timing_hypothesis": "24-48h",
                "source_mode": "memory_informed",
            },
            publish_result={"receipt_id": "r1", "media_id": "m1"},
            real_metrics={"source_status": "not_available_yet"},
        )
        self.assertEqual(result["recommended_next_format"], "carousel")
        self.assertIn("série", result["recommended_next_series_action"].lower())


if __name__ == "__main__":
    unittest.main()
