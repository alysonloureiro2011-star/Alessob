from __future__ import annotations

import unittest

from ace_next.distribution_timing_engine import build_distribution_timing_package
from ace_next.premium_eligibility_protocol import evaluate_premium_eligibility_protocol


class DistributionTimingEngineTests(unittest.TestCase):
    def test_reuses_recent_signal_when_window_has_evidence(self) -> None:
        result = build_distribution_timing_package(
            creative_plan={
                "publish_format_now": "reel",
                "headline": "clareza brutal",
                "hook": "o detalhe que mata retenção",
                "trend": "retenção real",
            },
            recent_records=[
                {
                    "content_format": "reel",
                    "published_at": "2026-03-20T18:50:00",
                    "real_metrics": {
                        "saved": 20,
                        "shares": 18,
                        "completion_rate": 88,
                        "watch_time_ms": 19000,
                    },
                },
                {
                    "content_format": "reel",
                    "published_at": "2026-03-22T18:50:00",
                    "real_metrics": {
                        "saved": 18,
                        "shares": 14,
                        "completion_rate": 84,
                        "watch_time_ms": 17000,
                    },
                },
                {
                    "content_format": "reel",
                    "published_at": "2026-03-21T11:40:00",
                    "real_metrics": {
                        "saved": 7,
                        "shares": 5,
                        "completion_rate": 52,
                        "watch_time_ms": 9000,
                    },
                },
            ],
            performance_context={"learning_state": "stable"},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["engine"], "DistributionTimingEngine")
        self.assertEqual(result["decision"]["recommended_window"], "18:50")
        self.assertIn("18:50", [
            result["decision"]["recommended_window"],
            *result["decision"]["backup_windows"],
        ])
        self.assertIn(result["decision"]["confidence"], {"medium", "high"})


class PremiumEligibilityProtocolTests(unittest.TestCase):
    def test_blocks_piece_when_brand_is_blocked(self) -> None:
        result = evaluate_premium_eligibility_protocol(
            editorial_qa={
                "approved": True,
                "breakdown": {
                    "perceived_value": 8.7,
                    "anti_commodity": 8.6,
                    "anti_genericity": 8.5,
                    "naturalism": 8.4,
                    "headline": 8.4,
                    "hook": 8.4,
                    "clarity": 8.5,
                },
            },
            visual_qa={"approved": True, "final_score": 86},
            perceptual_qa={
                "approved": True,
                "breakdown": {"composition": 8.4, "contrast": 8.5, "legibility": 8.6},
            },
            rubric_engine={
                "approved_minimum_quality": True,
                "global_score": 8.9,
                "global_score_100": 89,
                "breakdown": {"brand_fit": 8.9},
            },
            brand_veto_gate={"approved": False, "blocked": True},
            publication_authorization_gate={"selected_state": "editorial_staging"},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["classification"], "blocked_brand")
        self.assertTrue(result["blocked_by_brand"])
        self.assertFalse(result["brand_live_allowed_now"])

    def test_promotes_only_to_candidate_not_live(self) -> None:
        result = evaluate_premium_eligibility_protocol(
            editorial_qa={
                "approved": True,
                "breakdown": {
                    "perceived_value": 8.8,
                    "anti_commodity": 8.8,
                    "anti_genericity": 8.7,
                    "naturalism": 8.5,
                    "headline": 8.6,
                    "hook": 8.6,
                    "clarity": 8.7,
                },
            },
            visual_qa={"approved": True, "final_score": 87},
            perceptual_qa={
                "approved": True,
                "breakdown": {"composition": 8.7, "contrast": 8.7, "legibility": 8.8},
            },
            rubric_engine={
                "approved_minimum_quality": True,
                "global_score": 8.95,
                "global_score_100": 89.5,
                "breakdown": {"brand_fit": 9.0},
            },
            brand_veto_gate={"approved": True, "blocked": False},
            publication_authorization_gate={"selected_state": "editorial_staging"},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["classification"], "brand_live_candidate")
        self.assertTrue(result["eligible_for_brand_live_candidate"])
        self.assertFalse(result["brand_live_allowed_now"])
        self.assertTrue(result["requires_human_review"])


if __name__ == "__main__":
    unittest.main()
