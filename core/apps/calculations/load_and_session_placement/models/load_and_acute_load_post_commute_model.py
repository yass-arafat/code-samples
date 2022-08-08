from decimal import Decimal
from math import e


class LoadPostCommuteModel(object):
    def __init__(self, day):
        self.k_load = 42
        self.lambda_load = Decimal(e ** (-1 / self.k_load))
        self.day = day


class AcuteLoadPostCommute(object):
    def __init__(self, day):
        self.k_acute_load = 7
        self.lambda_acute_load = Decimal(e ** (-1 / self.k_acute_load))
        self.day = day
