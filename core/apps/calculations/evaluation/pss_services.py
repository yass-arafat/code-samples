from decimal import Decimal


class PssService:
    """Provides PSS related services"""

    def __init__(self, intensity, ride_duration):
        self.const = 100
        self.intensity = intensity
        self.ride_duration = ride_duration

    def get_pss(self):
        """Calculates and Returns PSS"""
        pss = (self.intensity**2) * self.ride_duration * self.const
        return Decimal(pss)
