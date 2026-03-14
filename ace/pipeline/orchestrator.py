import time

MAX_CYCLES = 50

class ACEPipelineController:

    def __init__(self):
        self.cycles = 0

    def allow_run(self):

        if self.cycles > MAX_CYCLES:
            return False

        self.cycles += 1
        return True


controller = ACEPipelineController()
