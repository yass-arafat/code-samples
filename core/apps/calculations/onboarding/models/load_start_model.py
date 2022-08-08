from decimal import Decimal


class PSSWeekModel(object):
    def __init__(self, hours_week):
        self.const1 = Decimal(100.00)
        self.hours_week = hours_week
        self.intensity_const = Decimal(0.7)


class LoadStartModel(object):
    def __init__(
        self, pss_daily_week1, pss_daily_week2, pss_daily_week3, pss_daily_week4
    ):
        self.pss_daily_week1 = pss_daily_week1
        self.pss_daily_week2 = pss_daily_week2
        self.pss_daily_week3 = pss_daily_week3
        self.pss_daily_week4 = pss_daily_week4
