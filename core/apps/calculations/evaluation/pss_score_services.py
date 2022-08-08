from decimal import Decimal


class PssScoreService:
    """Provides PSS related services"""

    def __init__(self, absolute_difference_pss):
        self.first_const = Decimal(-55)
        self.second_const = Decimal(116)
        self.third_const = Decimal(-65)
        self.fourth_const = Decimal(-6)
        self.fifth_const = Decimal(10)
        self.abs_diff_pss = absolute_difference_pss

    def get_pss_score(self):
        """Calculates and Returns PSS Score"""
        pss_score = (
            self.first_const * (self.abs_diff_pss**4)
            + self.second_const * (self.abs_diff_pss**3)
            + self.third_const * (self.abs_diff_pss**2)
            + self.fourth_const * self.abs_diff_pss
            + self.fifth_const
        )
        return pss_score
