import queue
import threading
import time


class QueueExecutor:

    def __init__(self):
        self.q = queue.Queue()
        self.running = False
        self.thread = None

    def add(self, task):
        self.q.put(task)

    def worker(self):
        while self.running:
            try:
                task = self.q.get(timeout=2)
                task()
                self.q.task_done()
            except queue.Empty:
                time.sleep(0.5)
            except Exception as e:
                print("QUEUE TASK ERROR:", e)

    def start(self):
        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self.worker,
            daemon=True
        )

        self.thread.start()

    def stop(self):
        self.running = False
