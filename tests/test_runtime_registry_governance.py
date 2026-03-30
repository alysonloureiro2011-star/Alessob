from __future__ import annotations

import unittest

from ace_next.runtime_registry import CURRENT_CAPABILITIES, FUTURE_CAPABILITIES, capability_names, resolve_capability


class RuntimeRegistryGovernanceTests(unittest.TestCase):
    def test_current_and_future_capabilities_do_not_overlap(self) -> None:
        current_names = {spec.name for spec in CURRENT_CAPABILITIES}
        future_names = {spec.name for spec in FUTURE_CAPABILITIES}
        self.assertTrue(current_names)
        self.assertTrue(future_names)
        self.assertEqual(current_names.intersection(future_names), set())

    def test_required_current_capabilities_resolve(self) -> None:
        required_names = [spec.name for spec in CURRENT_CAPABILITIES if spec.required]
        self.assertTrue(required_names)
        for name in required_names:
            resolved = resolve_capability(name)
            self.assertTrue(resolved["ok"], msg=f"required capability failed: {name} -> {resolved}")
            self.assertEqual(resolved["name"], name)

    def test_guarded_future_capabilities_remain_outside_current(self) -> None:
        current_names = set(capability_names(include_future=False))
        all_names = set(capability_names(include_future=True))
        guarded_future = {
            "DistributionTimingEngine",
            "SeoSocialEngine",
            "ThompsonSampler",
            "ExperimentRegistry",
            "RecommendationEngine",
            "NaturalismEngine",
            "DignityScore",
            "VisualHierarchyGate",
            "LLMOrchestrator",
            "ReflectionEngine",
            "SerialContinuityEngine",
        }
        for name in guarded_future:
            self.assertIn(name, all_names)
            self.assertNotIn(name, current_names)

    def test_current_reel_stack_remains_current(self) -> None:
        current_names = set(capability_names(include_future=False))
        expected_current = {
            "generate_hook_opening",
            "ReelStoryboardEngine",
            "ReelRhythmEngine",
            "PostProductionPipeline",
            "AudioDirectionLayer",
            "MultimodalReelQA",
            "CinematicGate",
            "ReleaseAuthority",
            "PublishGuard",
        }
        self.assertTrue(expected_current.issubset(current_names))


if __name__ == "__main__":
    unittest.main()
