from decimal import Decimal
from math import e


class InitialMaxLoad(object):
    def __init__(self, previous_load, ramp_rate):
        self.k_load = 42
        self.lambda_load = e ** (-1 / self.k_load)
        self.previous_load = (
            previous_load  # This is either starting load or last Sunday's load
        )
        self.ramp_rate = Decimal.from_float(ramp_rate)
