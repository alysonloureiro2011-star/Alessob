import unittest

from ace_next.authorization_hardening_pack import (
    BRAND_LIVE_CANDIDATE,
    EDITORIAL_STAGING,
    build_delta_to_brand_live,
    build_promotion_readiness_summary,
    decide_publication_state,
)


class AuthorizationHardeningPackTest(unittest.TestCase):
    def test_delta_to_brand_live(self):
        observed = {
            "perceived_value": 8.1,
            "brand_fit": 8.4,
            "anti_commodity": 8.2,
            "anti_genericity": 8.1,
            "global_score": 8.3,
            "hierarchy": 8.0,
            "clarity": 8.1,
            "headline": 8.0,
            "hook": 8.1,
            "naturalism": 8.0,
            "legibility": 8.2,
            "contrast": 8.0,
            "composition": 8.0,
        }
        delta = build_delta_to_brand_live(observed)
        self.assertIn("perceived_value", delta["missing_for_brand_live"])
        self.assertGreater(delta["score_gap_to_brand_live"], 0)

    def test_editorial_staging_state(self):
        observed = {
            "perceived_value": 8.0,
            "brand_fit": 8.4,
            "anti_commodity": 8.1,
            "anti_genericity": 8.1,
            "global_score": 8.1,
            "hierarchy": 8.0,
            "clarity": 8.0,
            "headline": 8.0,
            "hook": 8.0,
            "naturalism": 8.0,
            "legibility": 8.0,
            "contrast": 8.0,
            "composition": 8.0,
        }
        decision = decide_publication_state(
            force_placeholder=False,
            observed_scores=observed,
            brand_veto_blocked=False,
            require_human_review=True,
        )
        self.assertEqual(decision["selected_state"], EDITORIAL_STAGING)

    def test_brand_live_candidate_state(self):
        observed = {
            "perceived_value": 8.6,
            "brand_fit": 8.9,
            "anti_commodity": 8.7,
            "anti_genericity": 8.5,
            "global_score": 8.9,
            "hierarchy": 8.6,
            "clarity": 8.5,
            "headline": 8.0,
            "hook": 8.0,
            "naturalism": 8.1,
            "legibility": 8.0,
            "contrast": 8.0,
            "composition": 8.0,
        }
        decision = decide_publication_state(
            force_placeholder=False,
            observed_scores=observed,
            brand_veto_blocked=False,
            require_human_review=True,
        )
        self.assertEqual(decision["classification"], BRAND_LIVE_CANDIDATE)

    def test_promotion_readiness_summary(self):
        observed = {
            "perceived_value": 8.0,
            "brand_fit": 8.4,
            "anti_commodity": 8.1,
            "anti_genericity": 8.1,
            "global_score": 8.1,
            "hierarchy": 8.0,
            "clarity": 8.0,
            "headline": 8.0,
            "hook": 8.0,
            "naturalism": 8.0,
            "legibility": 8.0,
            "contrast": 8.0,
            "composition": 8.0,
        }
        summary = build_promotion_readiness_summary(
            observed_scores=observed,
            brand_veto_blocked=False,
            current_classification=EDITORIAL_STAGING,
        )
        self.assertIn("missing_for_brand_live", summary)
        self.assertIn("next_quality_lift_targets", summary)


if __name__ == "__main__":
    unittest.main()
