import threading
import time
import datetime


class CycleGuard:
    def __init__(self):
        self._cycle_lock = threading.Lock()
        self._video_lock = threading.Lock()

        self.state = {
            "cycle_running": False,
            "last_cycle": None,
            "video_lock": False,
            "cycles": 0,
            "last_error": None,
            "last_duration_sec": None
        }

        self._started_at = None

    def guard_cycle(self):
        acquired = self._cycle_lock.acquire(blocking=False)

        if not acquired:
            return False

        self.state["cycle_running"] = True
        self.state["last_cycle"] = datetime.datetime.utcnow().isoformat()
        self.state["last_error"] = None
        self._started_at = time.time()
        return True

    def release_cycle(self, error=None):
        if self._cycle_lock.locked():
            try:
                self._cycle_lock.release()
            except Exception:
                pass

        self.state["cycle_running"] = False
        self.state["cycles"] += 1

        if self._started_at:
            self.state["last_duration_sec"] = round(time.time() - self._started_at, 2)
        else:
            self.state["last_duration_sec"] = None

        self.state["last_error"] = error
        self._started_at = None

    def guard_video(self):
        acquired = self._video_lock.acquire(blocking=False)

        if not acquired:
            return False

        self.state["video_lock"] = True
        return True

    def release_video(self):
        if self._video_lock.locked():
            try:
                self._video_lock.release()
            except Exception:
                pass

        self.state["video_lock"] = False

    def snapshot(self):
        return {
            "cycle_running": self.state["cycle_running"],
            "last_cycle": self.state["last_cycle"],
            "video_lock": self.state["video_lock"],
            "cycles": self.state["cycles"],
            "last_error": self.state["last_error"],
            "last_duration_sec": self.state["last_duration_sec"]
        }


cycle_guard = CycleGuard()
