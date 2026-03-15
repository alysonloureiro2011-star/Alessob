import threading
import time

class CycleGuard:

    def __init__(self):
        self._lock = threading.Lock()
        self._running = False
        self._last_run = None

    def acquire(self):

        if self._lock.locked():
            return False

        acquired = self._lock.acquire(blocking=False)

        if acquired:
            self._running = True
            self._last_run = time.time()

        return acquired

    def release(self):

        if self._lock.locked():
            self._lock.release()

        self._running = False

    def status(self):

        return {
            "running": self._running,
            "last_run": self._last_run
        }

cycle_guard = CycleGuard()
