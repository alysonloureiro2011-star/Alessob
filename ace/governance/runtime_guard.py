def safe_call(func, *args, **kwargs):

    try:
        result = func(*args, **kwargs)

        if result is None:
            return {"ok": False, "error": "none_return"}

        return result

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }
