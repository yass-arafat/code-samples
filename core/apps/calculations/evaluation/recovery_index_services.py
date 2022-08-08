from decimal import Decimal


class RecoveryIndexService:
    """Provides Recovery Index related services"""

    def __init__(self, freshness):
        self.first_const = Decimal(-0.0002)
        self.second_const = Decimal(-0.0191)
        self.third_const = Decimal(0.313)
        self.freshness = freshness

    def get_recovery_index(self):
        """Calculates and Returns Recovery Index"""
        recovery_index = self.freshness * (
            self.first_const * (self.freshness**2)
            + self.second_const * self.freshness
            + self.third_const
        )
        return recovery_index
