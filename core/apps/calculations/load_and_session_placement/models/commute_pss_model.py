from decimal import Decimal


class CommutePSSModel(object):
    def __init__(self, time_commute_in_hours):
        self.constant1 = Decimal(2.00)
        self.time_commute_in_hours = time_commute_in_hours
        self.intensity_commute_constant = Decimal(0.65)
        self.constant2 = Decimal(100.00)
