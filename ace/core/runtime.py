# ==========================================================
# ACE Ω — RUNTIME GOVERNANCE
# ==========================================================

import time

class RuntimeState:

    def __init__(self):

        self.cycle_running = False
        self.last_cycle = None
        self.cycles = 0

    def start_cycle(self):

        if self.cycle_running:
            return False

        self.cycle_running = True
        self.last_cycle = time.time()
        return True

    def finish_cycle(self):

        self.cycle_running = False
        self.cycles += 1
