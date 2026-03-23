"bridge_state": (record.get("evidence_interpreter") or {}).get("bridge_state"),
"has_real_receipt": bool((record.get("publish_result") or {}).get("receipt_id")),
"has_media_id": bool((record.get("publish_result") or {}).get("media_id")),
"has_permalink": bool((record.get("publish_result") or {}).get("permalink")),
