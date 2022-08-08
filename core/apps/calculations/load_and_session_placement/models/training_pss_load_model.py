from decimal import Decimal
from math import e


class TrainingPSSLoad(object):
    def __init__(self, day):
        self.k_load = 42
        self.lambda_load = Decimal(e ** (-1 / self.k_load))
        self.max_load = day.max_load
        self.day = day
