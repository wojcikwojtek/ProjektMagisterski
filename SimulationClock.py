import time 

class SimulationClock:
    def __init__(self):
        self.start_real = time.time()
        self.paused_time = 0.0
        self.speed = 100.0
        self.paused = True

    def now(self):
        if self.paused:
            return self.paused_time
        
        real_elapsed = time.time() - self.start_real
        return self.paused_time + real_elapsed * self.speed
    
    def pause(self):
        if not self.paused:
            elapsed_time = time.time() - self.start_real
            self.paused_time += elapsed_time * self.speed
            self.paused = True
    
    def resume(self):
        if self.paused:
            self.start_real = time.time()
            self.paused = False

    def set_value(self, paused_time):
        self.paused_time = paused_time
        self.start_real = time.time()