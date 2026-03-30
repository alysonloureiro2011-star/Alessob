from __future__ import annotations

import unittest
from unittest.mock import patch

from ace_next.official_runtime_surface import OfficialRuntimeSurface


class _DummyConfig:
    pass


class _DummyRuntime:
    def __init__(self, payload: dict | None = None) -> None:
        self.payload = payload or {"ok": True, "source": "runtime"}
        self.calls = []

    def run(self, **kwargs) -> dict:
        self.calls.append(kwargs)
        return dict(self.payload)


class OfficialRuntimeSurfacePersistenceContractTests(unittest.TestCase):
    def test_run_attaches_runtime_cycle_persistence_outputs(self) -> None:
        surface = OfficialRuntimeSurface(_DummyConfig())
        surface.runtime = _DummyRuntime(
            {
                "ok": True,
                "source": "runtime",
                "performance_ingest": {"real_metrics": {"saved": 2}},
            }
        )

        persisted_payload = {
            "ok": True,
            "performance_store": {"saved": 2, "shares": 1},
            "learning_loop": {"planner_feedback_applied": True},
            "cycle_id": "cycle-123",
        }

        with patch("ace_next.official_runtime_surface.persist_runtime_cycle", return_value=persisted_payload) as mocked_persist:
            result = surface.run(
                trend="clareza",
                force_placeholder=False,
                force_real_probe=False,
                probe_state="auto",
                feedback_payload={"real_metrics": {"shares": 1}},
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["runtime_cycle_persistence"], persisted_payload)
        self.assertEqual(result["performance_store"], persisted_payload["performance_store"])
        self.assertEqual(result["learning_loop"], persisted_payload["learning_loop"])
        mocked_persist.assert_called_once()

    def test_run_keeps_runtime_result_when_persistence_returns_non_dict(self) -> None:
        runtime_payload = {
            "ok": True,
            "source": "runtime",
            "real_metrics_contract": {"saved": 3},
        }
        surface = OfficialRuntimeSurface(_DummyConfig())
        surface.runtime = _DummyRuntime(runtime_payload)

        with patch("ace_next.official_runtime_surface.persist_runtime_cycle", return_value=None) as mocked_persist:
            result = surface.run(
                trend="disciplina",
                feedback_payload={"real_metrics": {"saved": 5}},
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["source"], "runtime")
        self.assertNotIn("runtime_cycle_persistence", result)
        self.assertEqual(result["real_metrics_contract"]["saved"], 5)
        mocked_persist.assert_called_once()


if __name__ == "__main__":
    unittest.main()
