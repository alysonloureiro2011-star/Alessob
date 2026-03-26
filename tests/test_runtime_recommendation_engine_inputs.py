import unittest

from ace_next.recommendation_engine import build_recommendation_engine


class RuntimeRecommendationEngineInputsTest(unittest.TestCase):
    def test_recommendation_engine_accepts_runtime_inputs(self):
        result = build_recommendation_engine(
            evidence_interpreter={"evidence_state": "receipt_with_media_id"},
            experiment_resolution={"resolution_state": "observe"},
            resonance_engine={"resonance_score": 0.7},
            reward_prediction={"reward_prediction_score": 0.6},
            attention_metrics={"breakdown": {"attention_score": 62}},
            operational_state="editorial_staging",
            episodic_memory={"episode_id": "ep_001"},
            serial_continuity={
                "linked_series_candidate": True,
                "continuity_state": "continuity_confirmed",
                "next_episode_seed": "o próximo erro de clareza",
            },
            distribution_context={
                "recommended_next_format": "carousel",
                "recommended_next_angle": "aprofundar utilidade concreta",
                "recommended_next_series_action": "continuar série",
                "recommended_timing_hypothesis": "24-48h",
                "source_mode": "memory_informed",
            },
            publish_result={"receipt_id": "receipt_1", "media_id": "media_1"},
            real_metrics={"source_status": "not_available_yet"},
        )

        self.assertEqual(result["recommended_next_format"], "carousel")
        self.assertTrue(result["learning_bridge"]["episodic_memory_seen"])
        self.assertTrue(result["learning_bridge"]["serial_context_seen"])
        self.assertTrue(result["learning_bridge"]["distribution_context_seen"])


if __name__ == "__main__":
    unittest.main()
