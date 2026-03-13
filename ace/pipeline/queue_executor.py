
import queue
import threading
import time


class QueueExecutor:

    def __init__(self):
        self.q = queue.Queue()
        self.running = False

    def add(self, task):
        self.q.put(task)

    def worker(self):
        while self.running:
            try:
                task = self.q.get(timeout=2)
                task()
                self.q.task_done()
            except queue.Empty:
                time.sleep(1)

    def start(self):
        if self.running:
            return

        self.running = True

        t = threading.Thread(target=self.worker, daemon=True)
        t.start()

    def stop(self):
        self.running = False
