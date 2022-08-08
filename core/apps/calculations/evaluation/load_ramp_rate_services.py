class LoadRampRateService:
    """Provides Load Ramp Rate related services"""

    def __init__(self, start_load, end_load):
        self.start_load = start_load
        self.end_load = end_load

    def get_load_ramp_rate(self):
        """Calculates Load Ramp Rate"""
        load_ramp_rate = self.end_load - self.start_load
        return load_ramp_rate
