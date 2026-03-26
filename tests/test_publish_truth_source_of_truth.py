import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from ace_next.publish import PublishService


class PublishTruthSourceOfTruthTest(unittest.TestCase):
    def test_last_publish_prefers_ace_next_storage(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            config = SimpleNamespace(
                data_dir=data_dir,
                public_media_base_url="https://example.com",
                ig_token=None,
                ig_id=None,
                enable_real_publish=False,
                graph_base_url="https://graph.facebook.com/v23.0",
            )

            receipt = {
                "receipt_id": "receipt_123",
                "publish_status": "published_real_probe",
                "media_id": "media_123",
                "permalink": "https://instagram.com/p/abc",
                "created_at": "2026-03-26T00:00:00",
            }
            error = {
                "receipt_id": "receipt_err",
                "publish_status": "error",
                "created_at": "2026-03-26T00:01:00",
            }
            episodic = {
                "episodes": [
                    {
                        "episode_id": "ep_001",
                        "created_at": "2026-03-26T00:02:00",
                        "evidence_state": "receipt_with_permalink",
                        "resolution_state": "observe",
                    }
                ]
            }
            performance = {
                "records": [
                    {
                        "record_id": "rec_001",
                        "created_at": "2026-03-26T00:03:00",
                        "receipt": receipt,
                    }
                ]
            }

            (data_dir / "ace_next_publish_receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
            (data_dir / "ace_next_publish_error.json").write_text(json.dumps(error), encoding="utf-8")
            (data_dir / "ace_next_episodic_performance_memory.json").write_text(json.dumps(episodic), encoding="utf-8")
            (data_dir / "ace_next_performance_store.json").write_text(json.dumps(performance), encoding="utf-8")

            service = PublishService(config)
            summary = service.last_publish()

            self.assertEqual(summary["source_of_truth"], "ace_next")
            self.assertEqual(summary["last_publish_receipt"]["receipt_id"], "receipt_123")
            self.assertEqual(summary["latest_media_id"], "media_123")
            self.assertEqual(summary["latest_permalink"], "https://instagram.com/p/abc")
            self.assertEqual(summary["latest_evidence_state"], "receipt_with_permalink")


if __name__ == "__main__":
    unittest.main()
