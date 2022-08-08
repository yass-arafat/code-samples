class FreshnessService:
    """Provides Freshness related services"""

    def __init__(self, load, acute_load):
        self.load = load
        self.acute_load = acute_load

    def get_freshness(self):
        """Calculates and Returns Freshness"""
        freshness = self.load - self.acute_load
        return freshness
