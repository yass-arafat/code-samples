class AbsoluteDifferenceIntensityService:
    """Provides Absolute Difference Intensity related services"""

    def __init__(self, planned_intensity, actual_intensity):
        self.planned_intensity = planned_intensity
        self.actual_intensity = actual_intensity

    def get_absolute_difference_intensity(self):
        """Calculates and Returns Absolute Difference Intensity"""
        if self.planned_intensity == 0:
            abs_diff_intensity = 1
        else:
            abs_diff_intensity = abs(
                (self.actual_intensity - self.planned_intensity)
                / self.planned_intensity
            )

        return 1 if abs_diff_intensity > 1 else abs_diff_intensity
