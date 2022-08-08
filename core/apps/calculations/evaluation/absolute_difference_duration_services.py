class AbsoluteDifferenceDurationService:
    """Provides Absolute Difference Duration related services"""

    def __init__(self, planned_duration, actual_duration):
        self.planned_duration = planned_duration
        self.actual_duration = actual_duration

    def get_absolute_difference_duration(self):
        """Calculates and Returns Absolute Difference Duration"""
        if self.planned_duration == 0:
            abs_diff_duration = 1
        else:
            abs_diff_duration = abs(
                (self.actual_duration - self.planned_duration) / self.planned_duration
            )

        return 1 if abs_diff_duration > 1 else abs_diff_duration
