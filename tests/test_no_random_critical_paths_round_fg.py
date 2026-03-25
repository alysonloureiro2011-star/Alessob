import pathlib
import unittest


class NoRandomCriticalPathsRoundFGTest(unittest.TestCase):
    def test_no_random_import_or_usage(self):
        base = pathlib.Path("ace_next")
        targets = [
            base / "episodic_serial_contract.py",
            base / "serial_continuity_engine_v1.py",
            base / "episodic_performance_memory.py",
            base / "experiment_learning_contract.py",
            base / "experiment_registry.py",
            base / "recommendation_engine.py",
            base / "learning_loop.py",
        ]
        for path in targets:
            content = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("import random", content)
            self.assertNotIn("random.", content)


if __name__ == "__main__":
    unittest.main()
