class AbsoluteDifferencePssService:
    """Provides Absolute Difference PSS related services"""

    def __init__(self, planned_pss, actual_pss):
        self.planned_pss = planned_pss
        self.actual_pss = actual_pss

    def get_absolute_difference_pss(self):
        """Calculates and Returns Absolute Difference PSS"""
        if self.planned_pss == 0:
            abs_diff_pss = 1
        else:
            abs_diff_pss = abs((self.actual_pss - self.planned_pss) / self.planned_pss)

        return 1 if abs_diff_pss > 1 else abs_diff_pss
