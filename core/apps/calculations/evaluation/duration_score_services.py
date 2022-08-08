from decimal import Decimal


class DurationScoreService:
    """Provides Duration Score related services"""

    def __init__(self, absolute_difference_duration):
        self.first_const = Decimal(-55)
        self.second_const = Decimal(116)
        self.third_const = Decimal(-65)
        self.fourth_const = Decimal(-6)
        self.fifth_const = Decimal(10)
        self.abs_diff_duration = absolute_difference_duration

    def get_duration_score(self):
        """Calculates and Returns Duration Score"""
        duration_score = (
            self.first_const * (self.abs_diff_duration**4)
            + self.second_const * (self.abs_diff_duration**3)
            + self.third_const * (self.abs_diff_duration**2)
            + self.fourth_const * self.abs_diff_duration
            + self.fifth_const
        )
        return duration_score
