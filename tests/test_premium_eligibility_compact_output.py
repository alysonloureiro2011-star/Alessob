import unittest

from ace_next.official_app import _compact_publish_test_payload


class PremiumEligibilityCompactOutputTest(unittest.TestCase):
    def test_publish_test_compact_exposes_premium_gaps(self):
        compact = _compact_publish_test_payload(
            {
                "ok": True,
                "authorization_state": "editorial_staging",
                "operational_state": "editorial_staging",
                "probe_requested": False,
                "probe_eligible": False,
                "probe_publish_executed": False,
                "probe_block_reason": None,
                "publish_result": {"publish_status": "not_published_surface_protected"},
                "evidence_interpreter": {"evidence_state": "no_receipt"},
                "experiment_resolution": {"resolution_state": "collecting"},
                "recommendation_engine": {
                    "recommended_action": "repeat_probe",
                    "next_best_step": "rodar probe explícito",
                },
                "creative_plan": {
                    "caption_gate_result": True,
                    "caption_gate_score": 8.2,
                },
                "publication_authorization_gate": {
                    "premium_classification": "editorial_staging",
                    "eligible_for_editorial_staging": True,
                    "eligible_for_brand_live_candidate": False,
                    "missing_for_brand_live": ["brand_fit", "anti_commodity"],
                    "score_gap_to_brand_live": 0.9,
                    "next_quality_lift_targets": [{"metric": "brand_fit"}],
                    "summary": "autorizado para editorial_staging",
                },
                "approved_for_premium_visual": True,
            }
        )

        self.assertEqual(compact["premium_classification"], "editorial_staging")
        self.assertTrue(compact["eligible_for_editorial_staging"])
        self.assertFalse(compact["eligible_for_brand_live_candidate"])
        self.assertTrue(compact["premium_visual_result"])


if __name__ == "__main__":
    unittest.main()
