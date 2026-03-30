from __future__ import annotations

import unittest

from ace_next.audio_direction_layer import AudioDirectionLayer
from ace_next.cinematic_gate import CinematicGate
from ace_next.multimodal_reel_qa import MultimodalReelQA
from ace_next.premium_eligibility_protocol import (
    BRAND_LIVE_CANDIDATE,
    BLOCKED_QUALITY,
    EDITORIAL_STAGING,
    INTERNAL_LAB,
    evaluate_premium_eligibility_protocol,
    premium_eligibility_protocol_examples,
)
from ace_next.subtitle_intelligence import build_subtitle_package


class SubtitleIntelligenceTests(unittest.TestCase):
    def test_builds_deterministic_cues_with_safe_limits(self) -> None:
        result = build_subtitle_package(
            script_text=(
                "Quase todo mundo tenta explicar demais. "
                "Quando a mensagem entra limpa, a retenção sobe e o replay acontece."
            ),
            content_type="reel",
            hook_text="Olha o erro invisível",
        )

        self.assertTrue(result["ok"])
        self.assertTrue(result["deterministic"])
        self.assertEqual(result["engine"], "SubtitleIntelligence")
        self.assertLessEqual(len(result["cues"]), 12)
        self.assertIsNotNone(result["hook_overlay"])
        self.assertEqual(result["cues"][0]["animation"], "hook_pop")
        self.assertEqual(result["cues"][0]["placement"], "center_lower_third")
        self.assertLessEqual(len(result["cues"][0]["text"]), 64)

    def test_emphasis_and_style_stay_readable(self) -> None:
        result = build_subtitle_package(
            script_text="Agora a prova real aparece e a verdade fica impossível de ignorar.",
            content_type="reel",
            hook_text="Atenção no detalhe",
        )

        first_cue = result["cues"][0]
        self.assertIn(first_cue["color_role"], {"high_contrast_primary", "accent_emphasis"})
        self.assertGreaterEqual(first_cue["end_ms"], first_cue["start_ms"])
        self.assertLessEqual(len(first_cue["emphasis_words"]), 2)


class AudioDirectionLayerTests(unittest.TestCase):
    def test_high_controlled_density_enables_accented_mix(self) -> None:
        result = AudioDirectionLayer().run(
            hook_opening={"opening_pattern": "authority_shock"},
            rhythm={"target_cut_density": "high_controlled"},
            post_production={"sound_strategy": "clean_bed_with_light_accents"},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["state"], "audio_direction_layer_ready")
        self.assertEqual(result["voice_mode"], "assertive_clear")
        self.assertEqual(result["music_mode"], "accented_bed")
        self.assertEqual(result["foley_mode"], "micro_hits")
        self.assertEqual(result["mix_mode"], "dynamic_mix")

    def test_balanced_case_stays_clean(self) -> None:
        result = AudioDirectionLayer().run(
            hook_opening={"opening_pattern": "soft_observation"},
            rhythm={"target_cut_density": "medium_controlled"},
            post_production={"sound_strategy": "minimal_clean_bed"},
        )

        self.assertEqual(result["voice_mode"], "balanced_clear")
        self.assertEqual(result["music_mode"], "clean_bed")
        self.assertEqual(result["foley_mode"], "light_texture")
        self.assertEqual(result["mix_mode"], "clean_mix")


class MultimodalAndCinematicGateTests(unittest.TestCase):
    def test_multimodal_qa_approves_premium_reel(self) -> None:
        result = MultimodalReelQA().run(
            visual_gate={"global_visual_score": 8.9},
            audio_gate={"global_audio_score": 8.6},
            reel_gate={"global_score": 8.8},
            naturalism={"naturalism_state": "naturalism_engine_ready"},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["state"], "multimodal_reel_qa_ready")
        self.assertTrue(result["approved"])
        self.assertGreaterEqual(result["global_score"], 8.4)

    def test_cinematic_gate_blocks_low_qa(self) -> None:
        result = CinematicGate().run(
            multimodal_qa={"global_score": 7.9},
            reel_director={"visual_mode": "cinematic_retention", "cut_mode": "precision_fast"},
            premium_decision={"overall_quality_score": 8.4},
        )

        self.assertTrue(result["ok"])
        self.assertFalse(result["approved"])
        self.assertEqual(result["state"], "cinematic_gate_ready")
        self.assertEqual(result["veto_reason"], "multimodal_qa_low")


class PremiumEligibilityProtocolTests(unittest.TestCase):
    def test_classifies_internal_lab_when_piece_is_not_ready_for_staging(self) -> None:
        result = evaluate_premium_eligibility_protocol(
            editorial_qa={
                "approved": True,
                "breakdown": {
                    "perceived_value": 7.5,
                    "anti_commodity": 7.7,
                    "anti_genericity": 7.8,
                    "naturalism": 7.7,
                    "headline": 8.0,
                    "hook": 7.9,
                    "clarity": 8.0,
                },
            },
            visual_qa={"approved": True, "final_score": 77},
            perceptual_qa={"approved": True, "breakdown": {"composition": 7.9, "contrast": 8.0, "legibility": 8.1}},
            rubric_engine={"approved_minimum_quality": True, "global_score": 8.0, "global_score_100": 80, "breakdown": {"brand_fit": 8.2}},
            brand_veto_gate={"approved": True, "blocked": False},
            publication_authorization_gate={"selected_state": "internal_lab"},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["classification"], INTERNAL_LAB)
        self.assertTrue(result["eligible_for_lab"])
        self.assertFalse(result["eligible_for_editorial_staging"])
        self.assertFalse(result["blocked_by_quality"])

    def test_classifies_editorial_staging_when_all_staging_floors_pass(self) -> None:
        result = evaluate_premium_eligibility_protocol(
            editorial_qa={
                "approved": True,
                "breakdown": {
                    "perceived_value": 8.0,
                    "anti_commodity": 8.2,
                    "anti_genericity": 8.1,
                    "naturalism": 8.0,
                    "headline": 8.2,
                    "hook": 8.1,
                    "clarity": 8.3,
                },
            },
            visual_qa={"approved": True, "final_score": 80},
            perceptual_qa={"approved": True, "breakdown": {"composition": 8.1, "contrast": 8.2, "legibility": 8.4}},
            rubric_engine={"approved_minimum_quality": True, "global_score": 8.2, "global_score_100": 82, "breakdown": {"brand_fit": 8.5}},
            brand_veto_gate={"approved": True, "blocked": False},
            publication_authorization_gate={"selected_state": "editorial_staging"},
        )

        self.assertEqual(result["classification"], EDITORIAL_STAGING)
        self.assertTrue(result["eligible_for_editorial_staging"])
        self.assertFalse(result["eligible_for_brand_live_candidate"])

    def test_classifies_brand_live_candidate_without_unlocking_real_publish(self) -> None:
        result = evaluate_premium_eligibility_protocol(
            editorial_qa={
                "approved": True,
                "breakdown": {
                    "perceived_value": 8.7,
                    "anti_commodity": 8.7,
                    "anti_genericity": 8.5,
                    "naturalism": 8.4,
                    "headline": 8.6,
                    "hook": 8.5,
                    "clarity": 8.7,
                },
            },
            visual_qa={"approved": True, "final_score": 86},
            perceptual_qa={"approved": True, "breakdown": {"composition": 8.6, "contrast": 8.7, "legibility": 8.8}},
            rubric_engine={"approved_minimum_quality": True, "global_score": 8.9, "global_score_100": 89, "breakdown": {"brand_fit": 8.9}},
            brand_veto_gate={"approved": True, "blocked": False},
            publication_authorization_gate={"selected_state": "editorial_staging", "can_publish_real": False},
        )

        self.assertEqual(result["classification"], BRAND_LIVE_CANDIDATE)
        self.assertTrue(result["eligible_for_brand_live_candidate"])
        self.assertTrue(result["requires_human_review"])
        self.assertFalse(result["brand_live_allowed_now"])

    def test_blocks_low_quality_piece(self) -> None:
        result = evaluate_premium_eligibility_protocol(
            editorial_qa={"approved": False, "breakdown": {"perceived_value": 6.8, "anti_commodity": 6.9, "anti_genericity": 6.7, "naturalism": 7.0}},
            visual_qa={"approved": False, "final_score": 64},
            perceptual_qa={"approved": False, "breakdown": {"composition": 6.8, "contrast": 7.0, "legibility": 7.1}},
            rubric_engine={"approved_minimum_quality": False, "global_score": 7.0, "global_score_100": 70, "breakdown": {"brand_fit": 7.2}},
            brand_veto_gate={"approved": True, "blocked": False},
            publication_authorization_gate={"selected_state": "internal_lab"},
        )

        self.assertEqual(result["classification"], BLOCKED_QUALITY)
        self.assertTrue(result["blocked_by_quality"])
        self.assertFalse(result["eligible_for_editorial_staging"])

    def test_examples_remain_governed(self) -> None:
        result = premium_eligibility_protocol_examples()

        self.assertTrue(result["ok"])
        self.assertEqual(result["lab_example"]["classification"], INTERNAL_LAB)
        self.assertEqual(result["staging_example"]["classification"], EDITORIAL_STAGING)
        self.assertEqual(result["brand_live_candidate_example"]["classification"], BRAND_LIVE_CANDIDATE)


if __name__ == "__main__":
    unittest.main()
