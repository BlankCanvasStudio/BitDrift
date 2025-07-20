#
#
# clock.py
#
# The clock modules manage the timekeeping, and in particular ensure that the
# relative time of the experiment is synced with the objective time
#
import time

class Clock:
    def __init__(self, offset):
        self.offset_zero = offset

    def go_forward(self, offset):
        self.offset_zero += offset

    def get_time(self): 
        return time.time() - self.offset_zero


