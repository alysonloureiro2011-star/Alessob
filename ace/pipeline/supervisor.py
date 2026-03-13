import threading
import time


class Supervisor:

    def __init__(self, queue_executor, tick_seconds=15):
        self.queue_executor = queue_executor
        self.tick_seconds = tick_seconds
        self.running = False
        self.thread = None

    def cycle(self):
        """
        Aqui entra a lógica principal do ACE.
        Por enquanto, deixamos só o esqueleto.
        """
        pass

    def worker(self):
        while self.running:
            try:
                self.cycle()
            except Exception as e:
                print("SUPERVISOR ERROR:", e)
            time.sleep(self.tick_seconds)

    def start(self):
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self.worker, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
