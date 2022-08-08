from decimal import Decimal


class TrainingPSSMaxRide(object):
    def __init__(self, day):
        self.const_max_single_ride_multiplier = Decimal(3.6)
        self.day = day
        self.pss_commute_nth_day = day.commute_pss_day
