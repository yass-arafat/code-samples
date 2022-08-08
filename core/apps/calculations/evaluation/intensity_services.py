import logging
from decimal import Decimal
from math import sqrt

logger = logging.getLogger(__name__)


class IntensityService:
    """Provides Intensity related services"""

    def __init__(
        self,
        weighted_power=None,
        average_power=None,
        ftp=None,
        average_heart_rate=None,
        fthr=None,
    ):
        self.PERCENTAGE_FTHR_LOWER_BOUND = 25
        self.PERCENTAGE_FTHR_UPPER_BOUND = 118

        # For getting intensity from power data
        self.weighted_power = weighted_power
        self.average_power = average_power
        self.ftp = ftp

        # For getting intensity from heart rate data
        self.average_heart_rate = average_heart_rate
        self.fthr = fthr

    def percentage_fthr_boundary_check(self, percentage_fthr):
        """Cheking percentage fthr is between 25 and 118"""

        if percentage_fthr < self.PERCENTAGE_FTHR_LOWER_BOUND:
            percentage_fthr = self.PERCENTAGE_FTHR_LOWER_BOUND
        if percentage_fthr > self.PERCENTAGE_FTHR_UPPER_BOUND:
            percentage_fthr = self.PERCENTAGE_FTHR_UPPER_BOUND
        return percentage_fthr

    def get_intensity_from_power(self):
        """Returns Intensity calculated from Weighted Power"""

        if (
            self.weighted_power is None or self.ftp is None
        ) and self.average_power is None:
            logger.error(
                "Weighted Power / Average Power or FTP shouldn't be null while calculating Intensity from "
                "Power data"
            )
            intensity = 0
        else:
            if self.weighted_power:
                intensity = self.weighted_power / self.ftp
            else:
                intensity = self.average_power / self.ftp

        return Decimal(intensity)

    def get_intensity_from_heart_rate(self):
        """Returns Intensity calculated from Heart Rate"""

        if self.average_heart_rate is None or self.fthr is None:
            logger.error(
                " Avg Heart Rate or FTHR shouldn't be null while calculating Intensity from Heart Rate data"
            )
            intensity = 0
        else:
            percentage_fthr = (
                0 if self.fthr == 0 else (self.average_heart_rate / self.fthr) * 100
            )
            percentage_fthr = self.percentage_fthr_boundary_check(percentage_fthr)

            intensity = (
                1.0215 - sqrt(1.0435 + 0.0112 * (24.974 - percentage_fthr))
            ) / 0.56

        return Decimal(intensity)
