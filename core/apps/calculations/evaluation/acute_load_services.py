from decimal import Decimal
from math import e


class AcuteLoadService:
    """Provides Acute Load related services"""

    def __init__(self, acute_load_yesterday, pss_today):
        self.k_acute_load = 7
        self.lambda_acute_load = Decimal(e ** (-1 / self.k_acute_load))
        self.acute_load_yesterday = acute_load_yesterday
        self.pss_today = pss_today

    def get_acute_load_today(self, is_onboarding_day):
        """Calculates and Returns Today's Acute Load"""
        if is_onboarding_day:
            acute_load_today = (
                self.acute_load_yesterday
                + (1 - self.lambda_acute_load) * self.pss_today
            )
        else:
            acute_load_today = (
                self.lambda_acute_load * self.acute_load_yesterday
                + (1 - self.lambda_acute_load) * self.pss_today
            )

        return acute_load_today

    def get_planned_acute_load(self):
        acute_load_today = (
            self.lambda_acute_load * self.acute_load_yesterday
            + (1 - self.lambda_acute_load) * self.pss_today
        )
        return acute_load_today
