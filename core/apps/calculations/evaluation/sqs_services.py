from decimal import Decimal
from math import e

from core.apps.common.const import STARTING_SQS


class SQSSessionService:
    """Provides SQS Session related services"""

    def __init__(self, absolute_difference_intensity):
        self.first_const = Decimal(-11.256)
        self.second_const = Decimal(32.534)
        self.third_const = Decimal(-30.827)
        self.fourth_const = Decimal(10.00)
        self.abs_diff_intensity = absolute_difference_intensity

    def get_sqs_session(self):
        """Calculates and Returns SQS Session"""
        sqs_session = (
            self.first_const * (self.abs_diff_intensity**3)
            + self.second_const * (self.abs_diff_intensity**2)
            + self.third_const * self.abs_diff_intensity
            + self.fourth_const
        )
        return sqs_session


class SqsTodayService:
    """Provides SQS Today related services"""

    def __init__(self, sqs_yesterday, sqs_session):
        self.k_sqs = 5
        self.lambda_sqs = Decimal(e ** (-1 / self.k_sqs))
        self.sqs_yesterday = sqs_yesterday
        self.sqs_session = sqs_session

    def get_sqs_today(self, zone_focus):
        """Calculates and Returns SQS Today"""
        if zone_focus == 0:
            if self.sqs_yesterday:
                sqs_today = self.sqs_yesterday
            else:
                sqs_today = (
                    STARTING_SQS  # Onboarding day SQS will be equal to settings.py SQS
                )
        else:
            sqs_today = (
                self.lambda_sqs * self.sqs_yesterday
                + (1 - self.lambda_sqs) * self.sqs_session
            )
        return sqs_today


class WeightingSqsService:
    """Provides Weighting SQS related services"""

    def __init__(self, sqs_today):
        self.first_const = Decimal(0.05)
        self.second_const = Decimal(0.75)
        self.sqs_today = sqs_today

    def get_weighting_sqs(self):
        """Calculates and Returns Weighting SQS"""
        weighting_sqs = self.first_const * self.sqs_today + self.second_const
        return weighting_sqs
