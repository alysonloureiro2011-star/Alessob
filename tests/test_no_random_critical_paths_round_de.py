import pathlib
import unittest


class NoRandomCriticalPathsRoundDETest(unittest.TestCase):
    def test_no_random_import_or_usage(self):
        base = pathlib.Path("ace_next")
        targets = [
            base / "authorization_hardening_pack.py",
            base / "perceived_value_rewriter.py",
            base / "rubric_engine.py",
            base / "brand_veto_gate.py",
            base / "publication_authorization_gate.py",
        ]
        for path in targets:
            content = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("import random", content)
            self.assertNotIn("random.", content)


if __name__ == "__main__":
    unittest.main()
