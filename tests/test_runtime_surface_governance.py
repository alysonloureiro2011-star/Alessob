from __future__ import annotations

import types
import unittest
from unittest.mock import patch

import ace_bot
from ace_next.official_runtime_surface import OfficialRuntimeSurface


class _DummyRuntime:
    def __init__(self) -> None:
        self.calls = []

    def snapshot(self) -> dict:
        self.calls.append(("snapshot", None))
        return {"ok": True, "source": "runtime"}

    def compact_runtime_summary(self) -> dict:
        self.calls.append(("compact_runtime_summary", None))
        return {"ok": True, "source": "runtime_compact"}

    def probe_readiness_summary(self) -> dict:
        self.calls.append(("probe_readiness_summary", None))
        return {"ok": True, "source": "runtime_probe"}

    def quality_gap_summary(self) -> dict:
        self.calls.append(("quality_gap_summary", None))
        return {"ok": True, "source": "runtime_quality_gap"}

    def last_publish_compact_summary(self) -> dict:
        self.calls.append(("last_publish_compact_summary", None))
        return {"ok": True, "source": "runtime_last_publish"}

    def sync_instagram_auth(self) -> dict:
        self.calls.append(("sync_instagram_auth", None))
        return {"ok": True, "source": "runtime_auth"}

    def run(self, **kwargs) -> dict:
        self.calls.append(("run", kwargs))
        return {"ok": True, "source": "runtime_run", "echo": kwargs}


class _DummyConfig:
    pass


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def get_json(self) -> dict:
        return dict(self._payload)


class OfficialRuntimeSurfaceTests(unittest.TestCase):
    def test_surface_only_delegates_to_runtime(self) -> None:
        runtime = _DummyRuntime()
        surface = OfficialRuntimeSurface(_DummyConfig())
        surface.runtime = runtime

        snapshot = surface.snapshot()
        probe = surface.probe_readiness_summary()
        quality_gap = surface.quality_gap_summary()
        last_publish = surface.last_publish_compact_summary()
        auth = surface.sync_instagram_auth()
        run_result = surface.run(
            trend="clareza brutal",
            force_placeholder=True,
            force_real_probe=False,
            probe_state="auto",
            feedback_payload={"real_metrics": {"saved": 4}},
        )

        self.assertEqual(snapshot["source"], "runtime")
        self.assertEqual(probe["source"], "runtime_probe")
        self.assertEqual(quality_gap["source"], "runtime_quality_gap")
        self.assertEqual(last_publish["source"], "runtime_last_publish")
        self.assertEqual(auth["source"], "runtime_auth")
        self.assertEqual(run_result["source"], "runtime_run")
        self.assertEqual(runtime.calls[0][0], "snapshot")
        self.assertEqual(runtime.calls[-1][0], "run")
        self.assertEqual(runtime.calls[-1][1]["trend"], "clareza brutal")
        self.assertTrue(runtime.calls[-1][1]["force_placeholder"])
        self.assertFalse(runtime.calls[-1][1]["force_real_probe"])
        self.assertEqual(runtime.calls[-1][1]["probe_state"], "auto")

    def test_feedback_merge_does_not_change_governance_flags(self) -> None:
        runtime = _DummyRuntime()
        surface = OfficialRuntimeSurface(_DummyConfig())
        surface.runtime = runtime

        result = surface.run(
            trend="disciplina prática",
            feedback_payload={
                "real_metrics": {"saved": 8},
                "attention_metrics": {"breakdown": {"attention_score": 8.2}},
                "recommendation_engine": {"recommended_action": "observe"},
                "reflection_memory": {"guardrails": {"can_autopublish": False}},
            },
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["real_metrics_contract"]["saved"], 8)
        self.assertEqual(result["attention_metrics"]["breakdown"]["attention_score"], 8.2)
        self.assertEqual(result["recommendation_engine"]["recommended_action"], "observe")
        self.assertFalse(result["reflection_memory"]["guardrails"]["can_autopublish"])


class AceBotGovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        ace_bot._surface = None

    def tearDown(self) -> None:
        ace_bot._surface = None

    def test_get_surface_boots_official_runtime_surface_once(self) -> None:
        fake_surface = object()
        with patch("ace_bot.load_config", return_value=_DummyConfig()), patch("ace_bot.OfficialRuntimeSurface", return_value=fake_surface) as mocked_surface:
            first = ace_bot.get_surface()
            second = ace_bot.get_surface()

        self.assertIs(first, fake_surface)
        self.assertIs(second, fake_surface)
        mocked_surface.assert_called_once()

    def test_feedback_payload_only_exposes_expected_contract(self) -> None:
        payload = ace_bot._feedback_payload(
            {
                "real_metrics": {"saved": 1},
                "attention_metrics": {"breakdown": {"attention_score": 8.0}},
                "performance_ingest": {"ok": True},
                "recommendation_engine": {"recommended_action": "observe"},
                "experiment_resolution": {"resolution_state": "collecting"},
                "experiment_registry": {"ok": True},
                "episodic_performance_memory": {"ok": True},
                "reflection_memory": {"ok": True},
                "next_cycle_hook_candidate": "gancho limpo",
                "unexpected": "should_not_pass",
            }
        )

        self.assertIn("real_metrics", payload)
        self.assertIn("recommendation_engine", payload)
        self.assertNotIn("unexpected", payload)

    def test_ext_run_uses_surface_run_without_parallel_path(self) -> None:
        fake_surface = types.SimpleNamespace(
            run=lambda **kwargs: {
                "ok": True,
                "path": "surface_run",
                "echo": kwargs,
            }
        )

        with patch("ace_bot.get_surface", return_value=fake_surface):
            with ace_bot.app.test_request_context(
                "/ext/run?trend=clareza&force_placeholder=1&force_real_probe=0&probe_state=auto"
            ):
                response = ace_bot.run_pipeline()

        payload = response.get_json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["path"], "surface_run")
        self.assertEqual(payload["echo"]["trend"], "clareza")
        self.assertTrue(payload["echo"]["force_placeholder"])
        self.assertFalse(payload["echo"]["force_real_probe"])
        self.assertEqual(payload["echo"]["probe_state"], "auto")


if __name__ == "__main__":
    unittest.main()
