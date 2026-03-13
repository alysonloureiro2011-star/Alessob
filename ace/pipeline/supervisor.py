import threading
import time


class Supervisor:

    def __init__(self, queue_executor, tick_seconds=15):
        self.queue_executor = queue_executor
        self.tick_seconds = tick_seconds
        self.running = False
        self.thread = None
        self.pipeline_runner = None

    def set_pipeline_runner(self, runner):
        self.pipeline_runner = runner

    def cycle(self):
        from ace.engines.trend_engine import build_trend_object

        trend_obj = build_trend_object("inteligencia artificial", 1.0)
        trend = trend_obj["topic"]

        if not self.pipeline_runner:
            print("Supervisor sem pipeline_runner")
            return

        try:
            result = self.pipeline_runner(trend)
            print("ACE pipeline executado:", result.get("published"))
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
