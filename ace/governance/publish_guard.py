def normalize_publish_result(result):

    if result is None:
        return {"ok": False, "error": "none_result"}

    if isinstance(result, dict) and "ok" not in result:
        result["ok"] = True

    return result
