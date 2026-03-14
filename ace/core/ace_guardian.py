
import traceback
import datetime

ACE_GUARDIAN_LOG = []


def safe_execute(fn, *args, **kwargs):
    try:
        return {
            "ok": True,
            "result": fn(*args, **kwargs)
        }

    except Exception as e:

        error = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "error": str(e),
            "trace": traceback.format_exc()
        }

        ACE_GUARDIAN_LOG.append(error)

        return {
            "ok": False,
            "error": error
        }


def guardian_status():

    return {
        "guardian_errors": len(ACE_GUARDIAN_LOG),
        "last_error": ACE_GUARDIAN_LOG[-1] if ACE_GUARDIAN_LOG else None
    }
