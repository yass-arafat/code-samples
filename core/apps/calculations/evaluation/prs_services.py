class PrsService:
    """Provides PRS related services"""

    def __init__(self, load_today, recovery_index, weighting_sqs):
        self.load_today = load_today
        self.recovery_index = recovery_index
        self.w_sqs = weighting_sqs

    def get_prs(self):
        """Calculates and Returns PRS"""
        prs = self.w_sqs * self.load_today + self.recovery_index
        return prs
