from __future__ import annotations

import unittest

from ace_next.reflection_engine import ReflectionEngine
from ace_next.serial_continuity_engine import build_serial_continuity


class ReflectionEngineTests(unittest.TestCase):
    def test_reflection_stays_conservative_when_signal_is_missing(self) -> None:
        result = ReflectionEngine().run(
            creative_plan={
                "topic_seed": "clareza operacional",
                "publish_format_now": "image",
            },
            real_metrics={
                "source_status": "not_available_yet",
            },
            recommendation_engine={
                "recommended_action": "repeat_probe",
            },
            attention_metrics={
                "breakdown": {
                    "attention_score": None,
                }
            },
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["reflection_state"], "reflection_engine_ready")
        self.assertEqual(result["performance_state"], "collecting_more_signal")
        self.assertEqual(result["recommended_action"], "repeat_probe")
        self.assertEqual(result["confidence_hint"], "low")
        self.assertEqual(result["guardrails"]["mode"], "reflection_only")
        self.assertFalse(result["guardrails"]["can_autopublish"])
        self.assertFalse(result["guardrails"]["can_change_brand_policy"])

    def test_reflection_marks_measured_cycle_when_metrics_exist(self) -> None:
        result = ReflectionEngine().run(
            creative_plan={
                "topic_seed": "disciplina prática",
                "publish_format_now": "reel",
            },
            real_metrics={
                "source_status": "collected",
            },
            recommendation_engine={
                "recommended_action": "promote_to_editorial_staging_candidate",
            },
            attention_metrics={
                "breakdown": {
                    "attention_score": 8.1,
                }
            },
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["performance_state"], "measured")
        self.assertEqual(result["recommended_action"], "promote_to_editorial_staging_candidate")
        self.assertEqual(result["confidence_hint"], "medium")
        self.assertIn("reflection_mode=conservative", result["reflection_notes"])
        self.assertIn("brand_policy_locked=true", result["reflection_notes"])
        self.assertIn("disciplina prática", result["insight"])
        self.assertIn("reel", result["next_hypothesis"])


class SerialContinuityEngineTests(unittest.TestCase):
    def test_seed_episode_defaults_to_application_when_memory_is_empty(self) -> None:
        result = build_serial_continuity(
            creative_plan={
                "topic_seed": "clareza",
                "hook_family": "discipline_reframe",
                "format_recommendation": "image",
                "series_name": "soberania prática",
                "narrative_tension": "ruído vs clareza",
                "payoff": "decisão limpa",
            },
            recent_memory=[],
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["episode_role"], "seed")
        self.assertEqual(result["continuation_type"], "aplicacao")
        self.assertEqual(result["linked_format_suggestion"], "carousel")
        self.assertEqual(result["series_name"], "soberania prática")
        self.assertIn("disciplina_reframe", result["callback_elements"])
        self.assertIn("ruído vs clareza", result["callback_elements"])
        self.assertIn("decisão limpa", result["callback_elements"])

    def test_origin_episode_uses_contrast_for_identity_break(self) -> None:
        result = build_serial_continuity(
            creative_plan={
                "topic_seed": "autodisciplina",
                "hook_family": "identity_break",
                "format_recommendation": "reel",
            },
            recent_memory=None,
        )

        self.assertEqual(result["episode_role"], "origin")
        self.assertEqual(result["continuation_type"], "contraste")
        self.assertEqual(result["linked_format_suggestion"], "reel")
        self.assertIn("o que parece autodisciplina", result["next_episode_seed"])

    def test_follow_up_episode_uses_memory_to_continue_series(self) -> None:
        result = build_serial_continuity(
            creative_plan={
                "topic_seed": "foco",
                "hook_family": "misread_reality",
                "format_recommendation": "image",
            },
            recent_memory=[{"headline": "ontem"}],
        )

        self.assertEqual(result["episode_role"], "follow_up")
        self.assertEqual(result["continuation_type"], "aprofundamento")
        self.assertIn("o custo de ignorar foco por mais 30 dias", result["next_episode_seed"])
        self.assertEqual(result["linked_format_suggestion"], "carousel")


if __name__ == "__main__":
    unittest.main()
