from decimal import Decimal


class SessionOverallScoreService:
    """Provides Session Overall Score related services"""

    def __init__(self, duration_score, pss_score, sqs_session):
        self.const = Decimal(3.00)
        self.duration_score = duration_score
        self.pss_score = pss_score
        self.sqs_session = sqs_session

    def get_session_overall_score(self):
        """Calculates and Returns Session Overall Score"""
        session_score_overall = (
            self.duration_score + self.pss_score + self.sqs_session
        ) / self.const
        return session_score_overall
