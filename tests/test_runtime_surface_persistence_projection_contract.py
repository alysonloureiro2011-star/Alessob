from __future__ import annotations

import unittest
from unittest.mock import patch

from ace_next.official_runtime_surface import OfficialRuntimeSurface


class _DummyConfig:
    pass


class _DummyRuntime:
    def __init__(self, payload: dict | None = None) -> None:
        self.payload = payload or {"ok": True, "source": "runtime"}

    def run(self, **kwargs) -> dict:
        return dict(self.payload)


class OfficialRuntimeSurfacePersistenceProjectionContractTests(unittest.TestCase):
    def test_run_projects_persistence_blocks_back_to_result(self) -> None:
        surface = OfficialRuntimeSurface(_DummyConfig())
        surface.runtime = _DummyRuntime({"ok": True, "source": "runtime"})
        persisted_payload = {
            "ok": True,
            "persisted": True,
            "performance_store": {"record_id": "cycle-1", "stored": True},
            "learning_loop": {"planner_feedback_applied": True, "summary": "applied"},
        }

        with patch("ace_next.official_runtime_surface.persist_runtime_cycle", return_value=persisted_payload):
            result = surface.run(trend="clareza")

        self.assertEqual(result["runtime_cycle_persistence"], persisted_payload)
        self.assertEqual(result["performance_store"], {"record_id": "cycle-1", "stored": True})
        self.assertEqual(result["learning_loop"], {"planner_feedback_applied": True, "summary": "applied"})

    def test_run_keeps_runtime_payload_when_persistence_returns_non_dict(self) -> None:
        surface = OfficialRuntimeSurface(_DummyConfig())
        runtime_payload = {"ok": True, "source": "runtime", "trend": "disciplina"}
        surface.runtime = _DummyRuntime(runtime_payload)

        with patch("ace_next.official_runtime_surface.persist_runtime_cycle", return_value=None):
            result = surface.run(trend="disciplina")

        self.assertEqual(result, runtime_payload)
        self.assertNotIn("runtime_cycle_persistence", result)
        self.assertNotIn("performance_store", result)
        self.assertNotIn("learning_loop", result)

    def test_run_does_not_project_empty_nested_blocks(self) -> None:
        surface = OfficialRuntimeSurface(_DummyConfig())
        surface.runtime = _DummyRuntime({"ok": True, "source": "runtime"})
        persisted_payload = {
            "ok": True,
            "persisted": True,
            "performance_store": {},
            "learning_loop": {},
        }

        with patch("ace_next.official_runtime_surface.persist_runtime_cycle", return_value=persisted_payload):
            result = surface.run(trend="foco")

        self.assertEqual(result["runtime_cycle_persistence"], persisted_payload)
        self.assertNotIn("performance_store", result)
        self.assertNotIn("learning_loop", result)


if __name__ == "__main__":
    unittest.main()
