import time
import threading

ACE_AUTOSCHEDULER_RUNNING = False
ACE_AUTOSCHEDULER_THREAD = None


def ace_autoscheduler_loop(run_fn, interval_seconds=3600):
    global ACE_AUTOSCHEDULER_RUNNING

    while ACE_AUTOSCHEDULER_RUNNING:
        try:
            run_fn()
        except Exception as e:
            print("ACE AUTOSCHEDULER ERROR:", e)

        time.sleep(interval_seconds)


def start_ace_autoscheduler(run_fn, interval_seconds=3600):
    global ACE_AUTOSCHEDULER_RUNNING, ACE_AUTOSCHEDULER_THREAD

    if ACE_AUTOSCHEDULER_RUNNING:
        return False

    ACE_AUTOSCHEDULER_RUNNING = True

    ACE_AUTOSCHEDULER_THREAD = threading.Thread(
        target=ace_autoscheduler_loop,
        args=(run_fn, interval_seconds),
        daemon=True
    )
    ACE_AUTOSCHEDULER_THREAD.start()
    return True


def stop_ace_autoscheduler():
    global ACE_AUTOSCHEDULER_RUNNING
    ACE_AUTOSCHEDULER_RUNNING = False
    return True


def ace_autoscheduler_status():
    return {
        "running": ACE_AUTOSCHEDULER_RUNNING
    }
