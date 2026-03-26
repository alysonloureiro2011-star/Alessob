import unittest

from ace_next.official_app import _compact_runtime_payload


class VisualPremiumBridgeOfficialRuntimeTest(unittest.TestCase):
    def test_runtime_compact_exposes_premium_visual_state(self):
        payload = _compact_runtime_payload(
            {
                "token_present": True,
                "ig_id_present": True,
                "enable_real_publish": True,
                "brand_surface_mode": "protected",
                "real_probe_allowed_states": ["internal_lab", "editorial_staging"],
                "performance_store": {},
                "experiment_registry": {},
                "episodic_performance_memory": {},
                "last_run_summary": {
                    "premium_classification": "editorial_staging",
                    "eligible_for_editorial_staging": True,
                    "eligible_for_brand_live_candidate": False,
                    "missing_for_brand_live": ["brand_fit"],
                    "score_gap_to_brand_live": 0.8,
                    "next_quality_lift_targets": [{"metric": "brand_fit"}],
                    "caption_gate_result": True,
                    "caption_gate_score": 8.3,
                    "premium_visual_result": True,
                    "publication_authorization_summary": "autorizado para editorial_staging",
                    "selected_template_id": "premium_template_01",
                    "premium_render_state": "ready",
                    "hardening_applied": True,
                },
            },
            {"source_of_truth": "ace_next"},
        )

        self.assertTrue(payload["premium_visual_result"])
        self.assertEqual(payload["premium_classification"], "editorial_staging")
        self.assertEqual(payload["selected_template_id"], "premium_template_01")


if __name__ == "__main__":
    unittest.main()
