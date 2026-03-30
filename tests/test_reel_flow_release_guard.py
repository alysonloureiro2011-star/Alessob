from __future__ import annotations

import unittest

from ace_next.hook_opening_engine import generate_hook_opening
from ace_next.post_production_pipeline import PostProductionPipeline
from ace_next.publish_guard import PublishGuard
from ace_next.reel_rhythm_engine import ReelRhythmEngine
from ace_next.reel_storyboard_engine import ReelStoryboardEngine
from ace_next.release_authority import ReleaseAuthority


class HookOpeningEngineTests(unittest.TestCase):
    def test_hook_opening_is_deterministic_for_same_seed(self) -> None:
        first = generate_hook_opening("retenção", style="authority", content_type="reel")
        second = generate_hook_opening("retenção", style="authority", content_type="reel")

        self.assertEqual(first, second)
        self.assertTrue(first["deterministic"])
        self.assertEqual(first["opening_pattern"], "curiosity_gap")
        self.assertEqual(len(first["pattern_interrupts"]), 2)
        self.assertNotEqual(first["pattern_interrupts"][0], first["pattern_interrupts"][1])
        self.assertGreaterEqual(first["intensity_score"], 0.74)
        self.assertLessEqual(first["intensity_score"], 0.92)

    def test_authority_non_reel_uses_authority_shock(self) -> None:
        result = generate_hook_opening("viralização", style="authority", content_type="carousel")
        self.assertEqual(result["opening_pattern"], "authority_shock")


class ReelFlowTests(unittest.TestCase):
    def test_storyboard_preserves_hook_thesis_development_cta_order(self) -> None:
        result = ReelStoryboardEngine().run(
            creative_plan={
                "headline": "O conteúdo trava antes do payoff",
                "hook": "Seu hook ainda está fraco",
                "body": "Sem tensão clara, a retenção morre cedo.",
                "cta": "salve para revisar depois",
            },
            hook_opening={"opening_text": "Seu hook ainda está fraco"},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["storyboard_state"], "reel_storyboard_ready")
        self.assertEqual(result["scene_count"], 4)
        self.assertEqual([scene["role"] for scene in result["scenes"]], ["hook", "thesis", "development", "cta"])

    def test_rhythm_engine_hardens_four_scene_reel(self) -> None:
        result = ReelRhythmEngine().run(
            storyboard={"scene_count": 4},
            hook_opening={"opening_pattern": "authority_shock"},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["rhythm_state"], "reel_rhythm_ready")
        self.assertEqual(result["target_cut_density"], "high_controlled")
        self.assertEqual(result["target_pattern_interrupt_window"], "3_to_5_seconds")
        self.assertEqual(result["dead_air_policy"], "zero_dead_air")
        self.assertEqual(result["subtitle_pacing_hint"], "short_emphasis_lines")
        self.assertIn("intro_lenta", result["forbidden_rhythm_traits"])

    def test_post_production_pipeline_chooses_premium_motion_and_sound(self) -> None:
        result = PostProductionPipeline().run(
            storyboard={"scene_count": 4},
            rhythm={"target_cut_density": "high_controlled"},
            subtitles={"emphasis_mode": "short_emphasis_lines"},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["post_state"], "post_production_ready")
        self.assertEqual(result["cut_strategy"], "cinematic_fast_precision")
        self.assertEqual(result["motion_strategy"], "micro_zoom_plus_clean_reframes")
        self.assertEqual(result["sound_strategy"], "accent_hits_plus_clean_bed")
        self.assertIn("brand_dignity", result["final_qc_focus"])
        self.assertIn("cara de template barato", result["forbidden_traits"])


class ReleaseAndPublishGuardTests(unittest.TestCase):
    def test_release_authority_approves_when_quality_and_operation_are_ready(self) -> None:
        result = ReleaseAuthority().run(
            cinematic_gate={"cinematic_score": 8.8, "approved": True},
            premium_decision={"overall_quality_score": 8.7},
            operation_bridge={"operational_state": "ready"},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["state"], "release_authority_ready")
        self.assertTrue(result["approved_for_publish"])
        self.assertFalse(result["blocked_by_quality"])
        self.assertEqual(result["release_state"], "APPROVED_FOR_PUBLISH")

    def test_release_authority_blocks_by_operation_state(self) -> None:
        result = ReleaseAuthority().run(
            cinematic_gate={"cinematic_score": 8.8, "approved": True},
            premium_decision={"overall_quality_score": 8.9},
            operation_bridge={"operational_state": "lab"},
        )

        self.assertFalse(result["approved_for_publish"])
        self.assertEqual(result["release_state"], "BLOCKED_BY_OPERATION_STATE")

    def test_publish_guard_ready_mode(self) -> None:
        result = PublishGuard().run(
            release_authority={"release_state": "APPROVED_FOR_PUBLISH", "approved_for_publish": True},
            publish_truth={"truth_state": "publish_attempt_recorded"},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["state"], "publish_guard_ready")
        self.assertEqual(result["mode"], "ready")
        self.assertTrue(result["can_publish"])
        self.assertEqual(result["next_step"], "publish_now")

    def test_publish_guard_done_mode_after_truth_confirmation(self) -> None:
        result = PublishGuard().run(
            release_authority={"release_state": "APPROVED_FOR_PUBLISH", "approved_for_publish": True},
            publish_truth={"truth_state": "publish_truth_confirmed"},
        )

        self.assertEqual(result["mode"], "done")
        self.assertFalse(result["can_publish"])
        self.assertEqual(result["next_step"], "measure_now")

    def test_publish_guard_blocks_when_release_is_not_approved(self) -> None:
        result = PublishGuard().run(
            release_authority={"release_state": "BLOCKED_BY_QUALITY", "approved_for_publish": False},
            publish_truth={"truth_state": "publish_truth_absent"},
        )

        self.assertEqual(result["mode"], "blocked")
        self.assertFalse(result["can_publish"])
        self.assertEqual(result["next_step"], "improve_quality")


if __name__ == "__main__":
    unittest.main()
