from decimal import Decimal

from core.apps.common.const import STARTING_SAS
from core.apps.common.utils import is_recovery_day


class SessionAccuracyScoreService:
    @staticmethod
    def get_absolute_difference(actual_value, planned_value):
        return (
            min(abs((actual_value - planned_value) / planned_value), 1)
            if planned_value
            else 1
        )

    @classmethod
    def calculate_accuracy_score(
        cls, actual_value: Decimal, planned_value: Decimal
    ) -> Decimal:
        first_const = Decimal(-64.103)
        second_const = Decimal(142.77)
        third_const = Decimal(-87.704)
        fourth_const = Decimal(4.2249)
        fifth_const = Decimal(-4.1923)
        sixth_const = Decimal(9.9965)
        absolute_diff = cls.get_absolute_difference(actual_value, planned_value)

        score = (
            first_const * (absolute_diff**5)
            + second_const * (absolute_diff**4)
            + third_const * (absolute_diff**3)
            + fourth_const * (absolute_diff**2)
            + fifth_const * absolute_diff
            + sixth_const
        )

        return Decimal(score * 10)

    @classmethod
    def calculate_key_zone_performance(
        cls, actual_time_in_key_zones: int, planned_time_in_key_zones: int
    ) -> Decimal:
        if not planned_time_in_key_zones:
            return Decimal(0)
        return Decimal(
            (actual_time_in_key_zones - planned_time_in_key_zones)
            / planned_time_in_key_zones
        )

    @classmethod
    def calculate_sas_today(
        cls,
        sas_yesterday: Decimal,
        overall_accuracy_score: Decimal or None,
        zone_focus: int,
    ) -> Decimal:
        # If overall_accuracy_score is None, that means overall_accuracy_score was not calculated
        # But if overall_accuracy_score is 0, that means it was calculated and the result is 0
        sas_session = overall_accuracy_score

        if is_recovery_day(zone_focus) or sas_session is None:
            # If the user has created the plan today, we won't have sas_yesterday,
            # so SQS_start will be returned instead.
            return sas_yesterday or STARTING_SAS

        smoothing_factor = 2
        days_considered = 10
        k_sas = smoothing_factor / (1 + days_considered)
        return (Decimal(sas_session) * Decimal(k_sas)) + (
            Decimal(sas_yesterday) * Decimal(1 - k_sas)
        )

    @classmethod
    def calculate_weighting_sas(cls, sas_today: Decimal) -> Decimal:
        first_const = Decimal(0.05)
        second_const = Decimal(0.75)
        return first_const * Decimal(sas_today / 10) + second_const
