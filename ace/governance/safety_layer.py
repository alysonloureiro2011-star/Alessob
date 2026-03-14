def safe_execute(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }
