from __future__ import annotations

import unittest

from ace_next.naturalism_engine import NaturalismEngine
from ace_next.super_orchestrator import AceSuperOrchestrator
from ace_next.trend_radar import TREND_FALLBACK, TrendRadar


class TrendRadarTests(unittest.TestCase):
    def test_weak_trend_uses_fallback(self) -> None:
        result = TrendRadar().run(
            trend="teste real",
            recent_signal_score=None,
            signal_context={"source": "unit_test"},
            source="unit_test",
        )

        self.assertTrue(result["ok"])
        self.assertTrue(result["weak_trend"])
        self.assertEqual(result["effective_trend"], TREND_FALLBACK)
        self.assertEqual(result["signal_strength"], "unknown")

    def test_strong_trend_preserves_effective_trend(self) -> None:
        result = TrendRadar().run(
            trend="disciplina e clareza mental",
            recent_signal_score=0.81,
            signal_context={"source": "unit_test"},
            source="unit_test",
        )

        self.assertTrue(result["ok"])
        self.assertFalse(result["weak_trend"])
        self.assertEqual(result["effective_trend"], "disciplina e clareza mental")
        self.assertEqual(result["signal_strength"], "strong")


class NaturalismEngineTests(unittest.TestCase):
    def test_reel_prefers_timing_humanization(self) -> None:
        result = NaturalismEngine().run(
            creative_plan={"publish_format_now": "reel"},
            visual_context={"template_id": "hook_reel_v1"},
        )

        self.assertTrue(result["ok"])
        self.assertTrue(result["apply_timing_humanization"])
        self.assertFalse(result["apply_layout_irregularity"])
        self.assertEqual(result["naturalism_state"], "naturalism_engine_ready")

    def test_image_prefers_layout_irregularity(self) -> None:
        result = NaturalismEngine().run(
            creative_plan={"publish_format_now": "image"},
            visual_context={"template_id": "hero_card_v1"},
        )

        self.assertTrue(result["ok"])
        self.assertFalse(result["apply_timing_humanization"])
        self.assertTrue(result["apply_layout_irregularity"])
        self.assertIn("evitar perfeicao plastica", result["guardrails"])


class _RuntimeWithInternal:
    def __init__(self) -> None:
        self.calls = []

    def _run_cycle_internal(self, **kwargs):
        self.calls.append(("internal", kwargs))
        return {"ok": True, "path": "internal"}


class _RuntimeWithoutInternal:
    def __init__(self) -> None:
        self.calls = []

    def run(self, **kwargs):
        self.calls.append(("run", kwargs))
        return {"ok": True, "path": "run"}


class _DummyConfig:
    pass


class SuperOrchestratorTests(unittest.TestCase):
    def test_prefers_internal_runtime_path(self) -> None:
        runtime = _RuntimeWithInternal()
        orchestrator = AceSuperOrchestrator(_DummyConfig())

        result = orchestrator.run(
            runtime,
            trend="clareza brutal",
            force_placeholder="true",
            force_real_probe="false",
            probe_state="invalid_state",
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["path"], "internal")
        self.assertEqual(result["execution_surface"], "super_orchestrator")
        self.assertEqual(result["execution_envelope"]["request"]["trend"], "clareza brutal")
        self.assertTrue(result["execution_envelope"]["request"]["force_placeholder"])
        self.assertFalse(result["execution_envelope"]["request"]["force_real_probe"])
        self.assertEqual(result["execution_envelope"]["request"]["probe_state"], "auto")
        self.assertEqual(runtime.calls[0][0], "internal")

    def test_falls_back_to_runtime_run(self) -> None:
        runtime = _RuntimeWithoutInternal()
        orchestrator = AceSuperOrchestrator(_DummyConfig())

        result = orchestrator.run(
            runtime,
            trend="clareza operacional",
            force_placeholder=False,
            force_real_probe=True,
            probe_state="editorial_staging",
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["path"], "run")
        self.assertEqual(result["execution_envelope"]["request"]["probe_state"], "editorial_staging")
        self.assertTrue(result["execution_envelope"]["request"]["force_real_probe"])
        self.assertEqual(runtime.calls[0][0], "run")


if __name__ == "__main__":
    unittest.main()
