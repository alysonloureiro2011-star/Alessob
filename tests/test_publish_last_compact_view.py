import unittest

from ace_next.official_app import (
    _compact_last_publish_payload,
    _compact_publish_test_payload,
    _compact_runtime_payload,
)


class PublishLastCompactViewTest(unittest.TestCase):
    def test_compact_last_publish_payload(self):
        payload = _compact_last_publish_payload(
            {
                "source_of_truth": "ace_next",
                "last_publish_receipt": {
                    "receipt_id": "receipt_1",
                    "publish_status": "published_real_probe",
                    "media_id": "media_1",
                    "permalink": "https://instagram.com/p/1",
                },
                "latest_evidence_state": "receipt_with_permalink",
                "latest_resolution_state": "observe",
                "total_records": 3,
                "total_episodes": 2,
            }
        )
        self.assertEqual(payload["receipt_id"], "receipt_1")
        self.assertEqual(payload["media_id"], "media_1")

    def test_compact_runtime_payload(self):
        compact = _compact_runtime_payload(
            {
                "token_present": True,
                "ig_id_present": True,
                "enable_real_publish": True,
                "brand_surface_mode": "protected",
                "real_probe_allowed_states": ["internal_lab", "editorial_staging"],
                "performance_store": {
                    "total_records": 5,
                    "latest_receipt_id": "receipt_1",
                    "latest_media_id": "media_1",
                    "latest_permalink": "https://instagram.com/p/1",
                    "latest_probe_requested": True,
                    "latest_probe_publish_executed": True,
                    "latest_evidence_bridge_state": "receipt_with_permalink",
                },
                "experiment_registry": {
                    "total_experiments": 2,
                    "latest_experiment_state": "editorial_staging",
                    "latest_resolution_state": "observe",
                },
                "episodic_performance_memory": {
                    "total_episodes": 2,
                    "latest_episode_id": "ep_1",
                    "latest_continuity_state": "continuity_hypothesis",
                    "latest_series_name": "Liberta a Verdade",
                },
            },
            {
                "source_of_truth": "ace_next",
                "last_publish_receipt": {"receipt_id": "receipt_1"},
            },
        )
        self.assertTrue(compact["token_present"])
        self.assertEqual(compact["performance_store"]["latest_receipt_id"], "receipt_1")

    def test_compact_publish_test_payload(self):
        compact = _compact_publish_test_payload(
            {
                "ok": True,
                "authorization_state": "editorial_staging",
                "operational_state": "editorial_staging",
                "probe_requested": True,
                "probe_eligible": True,
                "probe_publish_executed": False,
                "probe_block_reason": None,
                "publish_result": {
                    "publish_status": "error",
                    "receipt_id": "receipt_1",
                },
                "evidence_interpreter": {"evidence_state": "receipt_only"},
                "experiment_resolution": {"resolution_state": "collecting"},
                "recommendation_engine": {
                    "recommended_action": "wait_metrics",
                    "next_best_step": "aguardar nova leitura",
                },
            }
        )
        self.assertEqual(compact["receipt_id"], "receipt_1")
        self.assertEqual(compact["recommended_action"], "wait_metrics")


if __name__ == "__main__":
    unittest.main()
