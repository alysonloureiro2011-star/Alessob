from __future__ import annotations

import unittest

from ace_next.official_runtime_surface import OfficialRuntimeSurface


class _DummyConfig:
    pass


class _DummyRuntime:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def snapshot(self) -> dict:
        self.calls.append("snapshot")
        return {"ok": True, "source": "runtime_snapshot"}

    def compact_runtime_summary(self) -> dict:
        self.calls.append("compact_runtime_summary")
        return {"ok": True, "source": "runtime_compact"}

    def probe_readiness_summary(self) -> dict:
        self.calls.append("probe_readiness_summary")
        return {"ok": True, "source": "probe_readiness"}

    def quality_gap_summary(self) -> dict:
        self.calls.append("quality_gap_summary")
        return {"ok": True, "source": "quality_gap"}

    def last_publish_compact_summary(self) -> dict:
        self.calls.append("last_publish_compact_summary")
        return {"ok": True, "source": "last_publish"}

    def sync_instagram_auth(self) -> dict:
        self.calls.append("sync_instagram_auth")
        return {"ok": True, "source": "auth_sync"}


class OfficialRuntimeSurfaceReadonlyContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.surface = OfficialRuntimeSurface(_DummyConfig())
        self.surface.runtime = _DummyRuntime()

    def test_snapshot_delegates_without_transforming(self) -> None:
        result = self.surface.snapshot()
        self.assertEqual(result, {"ok": True, "source": "runtime_snapshot"})
        self.assertEqual(self.surface.runtime.calls, ["snapshot"])

    def test_compact_runtime_summary_delegates_without_transforming(self) -> None:
        result = self.surface.compact_runtime_summary()
        self.assertEqual(result, {"ok": True, "source": "runtime_compact"})
        self.assertEqual(self.surface.runtime.calls, ["compact_runtime_summary"])

    def test_probe_readiness_summary_delegates_without_transforming(self) -> None:
        result = self.surface.probe_readiness_summary()
        self.assertEqual(result, {"ok": True, "source": "probe_readiness"})
        self.assertEqual(self.surface.runtime.calls, ["probe_readiness_summary"])

    def test_quality_gap_summary_delegates_without_transforming(self) -> None:
        result = self.surface.quality_gap_summary()
        self.assertEqual(result, {"ok": True, "source": "quality_gap"})
        self.assertEqual(self.surface.runtime.calls, ["quality_gap_summary"])

    def test_last_publish_compact_summary_delegates_without_transforming(self) -> None:
        result = self.surface.last_publish_compact_summary()
        self.assertEqual(result, {"ok": True, "source": "last_publish"})
        self.assertEqual(self.surface.runtime.calls, ["last_publish_compact_summary"])

    def test_sync_instagram_auth_delegates_without_transforming(self) -> None:
        result = self.surface.sync_instagram_auth()
        self.assertEqual(result, {"ok": True, "source": "auth_sync"})
        self.assertEqual(self.surface.runtime.calls, ["sync_instagram_auth"])


if __name__ == "__main__":
    unittest.main()
