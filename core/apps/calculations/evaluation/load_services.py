from decimal import Decimal
from math import e


class LoadService:
    """Provides Load related services"""

    def __init__(self, load_yesterday, pss_today):
        self.k_load = 42
        self.lambda_load = Decimal(e ** (-1 / self.k_load))
        self.load_yesterday = load_yesterday
        self.pss_today = pss_today

    def get_load_today(self, is_onboarding_day):
        """Calculates and Returns Today's Load"""
        if is_onboarding_day:
            load_today = self.load_yesterday + (1 - self.lambda_load) * self.pss_today
        else:
            load_today = (
                self.lambda_load * self.load_yesterday
                + (1 - self.lambda_load) * self.pss_today
            )

        return load_today

    def get_planned_load(self):
        load_today = (
            self.lambda_load * self.load_yesterday
            + (1 - self.lambda_load) * self.pss_today
        )
        return load_today
