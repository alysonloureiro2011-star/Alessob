import threading
import time


class Supervisor:

    def __init__(self, queue_executor, tick_seconds=15):
        self.queue_executor = queue_executor
        self.tick_seconds = tick_seconds
        self.running = False
        self.thread = None

    
def cycle(self):

    from ace.engines.trend_engine import build_trend_object
    from ace_bot import ace_run_modular_pipeline

    trend_obj = build_trend_object("disciplina e prosperidade", 1.0)

    trend = trend_obj["topic"]

    try:

        result = ace_run_modular_pipeline(trend)

        print("ACE pipeline executado:", result["published"])

    except Exception as e:

        print("Erro no pipeline:", e)
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
