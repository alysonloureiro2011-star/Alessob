from __future__ import annotations

import unittest
from unittest.mock import patch

from ace_next.official_runtime_surface import OfficialRuntimeSurface


class _DummyConfig:
    pass


class _DummyRuntime:
    def __init__(self, payload: dict | None = None) -> None:
        self.payload = payload or {"ok": True, "source": "runtime"}
        self.calls: list[dict] = []

    def run(self, **kwargs) -> dict:
        self.calls.append(kwargs)
        return dict(self.payload)


class OfficialRuntimeSurfaceRunDelegationContractTests(unittest.TestCase):
    def test_run_forwards_control_flags_without_transforming_them(self) -> None:
        surface = OfficialRuntimeSurface(_DummyConfig())
        runtime = _DummyRuntime({"ok": True, "source": "runtime"})
        surface.runtime = runtime

        with patch("ace_next.official_runtime_surface.persist_runtime_cycle", return_value={"ok": True}):
            result = surface.run(
                trend="clareza",
                force_placeholder=True,
                force_real_probe=True,
                probe_state="manual_probe",
                feedback_payload=None,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(
            runtime.calls,
            [
                {
                    "trend": "clareza",
                    "force_placeholder": True,
                    "force_real_probe": True,
                    "probe_state": "manual_probe",
                }
            ],
        )

    def test_run_forwards_default_flags_when_not_overridden(self) -> None:
        surface = OfficialRuntimeSurface(_DummyConfig())
        runtime = _DummyRuntime({"ok": True, "source": "runtime"})
        surface.runtime = runtime

        with patch("ace_next.official_runtime_surface.persist_runtime_cycle", return_value={"ok": True}):
            result = surface.run(trend="disciplina")

        self.assertTrue(result["ok"])
        self.assertEqual(
            runtime.calls,
            [
                {
                    "trend": "disciplina",
                    "force_placeholder": False,
                    "force_real_probe": False,
                    "probe_state": None,
                }
            ],
        )

    def test_run_persists_the_merged_runtime_result(self) -> None:
        surface = OfficialRuntimeSurface(_DummyConfig())
        runtime = _DummyRuntime(
            {
                "ok": True,
                "source": "runtime",
                "performance_ingest": {"real_metrics": {"shares": 1}},
            }
        )
        surface.runtime = runtime

        with patch("ace_next.official_runtime_surface.persist_runtime_cycle", return_value={"ok": True}) as mocked_persist:
            result = surface.run(
                trend="foco",
                feedback_payload={
                    "real_metrics": {"saved": 2},
                    "next_cycle_hook_candidate": "o que voce ainda nao percebeu?",
                },
            )

        self.assertTrue(result["ok"])
        mocked_persist.assert_called_once()
        persisted_arg = mocked_persist.call_args.args[1]
        self.assertEqual(persisted_arg["performance_ingest"]["real_metrics"], {"shares": 1, "saved": 2})
        self.assertEqual(persisted_arg["real_metrics_contract"], {"saved": 2})
        self.assertEqual(persisted_arg["next_cycle_hook_candidate"], "o que voce ainda nao percebeu?")


if __name__ == "__main__":
    unittest.main()
