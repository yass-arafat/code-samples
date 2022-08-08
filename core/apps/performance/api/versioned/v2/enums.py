import logging
from enum import Enum

from core.apps.common.const import CHRONIC_LOAD_BUFFER, LOAD_OVERTRAINING_LIMIT
from core.apps.common.services import RoundServices

logger = logging.getLogger(__name__)


class FreshnessPerformanceEnum(Enum):
    # Title text
    CONSIDERABLE_FATIGUE = "Considerable Fatigue"
    ACCUMULATING_FATIGUE = "Accumulating Fatigue"
    MINIMAL_FATIGUE = "Minimal Fatigue"

    # Remarks text
    RECOVERING_REMARKS = (
        "You have been giving yourself time to recover over the last week, "
        "try and complete some more training soon."
    )
    PROGRESSING_REMARKS = "You have been completing some productive training over the last week, keep it up!"
    OVERTRAINING_REMARKS = (
        "Over the last week you have trained more than you typically do, "
        "make sure you take time to recover."
    )
    DEFAULT_REMARKS = (
        "As you complete training over the next week your freshness value will be "
        "calculated to monitor your fatigue."
    )

    @classmethod
    def get_title_text(cls, freshness_value):
        # For now, we are using the title text from FreshnessStateEnum
        # to maintain consistency
        return FreshnessStateEnum.get_freshness_state(freshness_value)

    @classmethod
    def get_remarks_text(cls, freshness_values=None, is_onboarding_week=False):
        if is_onboarding_week:
            return cls.DEFAULT_REMARKS.value

        undertraining_count = 0
        effective_training_count = 0
        overtraining_count = 0
        for freshness_value in freshness_values:
            if freshness_value < -10:
                overtraining_count += 1
            elif freshness_value < 0:
                effective_training_count += 1
            else:
                undertraining_count += 1

        # overtraining has highest priority, so it is checked first, then effective and lastly undertraining
        if overtraining_count >= max(effective_training_count, undertraining_count):
            return cls.OVERTRAINING_REMARKS.value
        if effective_training_count >= max(overtraining_count, undertraining_count):
            return cls.PROGRESSING_REMARKS.value
        return cls.RECOVERING_REMARKS.value


class TrainingLoadPerformanceEnum(Enum):
    # Performance text (title, remarks)
    HIGH_RISK_FATIGUE = (
        "High-Risk Fatigue",
        "Your chronic training load has increased significantly over the last two "
        "weeks, trying to increase your fitness too quickly will increase the risk of "
        "injury and overtraining!",
    )
    INCREASING_FITNESS = (
        "Increasing Fitness",
        "Your chronic training load has increased by {load_change} over the "
        "last two weeks, you will notice the fitness benefits!",
    )
    MAINTAINING_FITNESS = (
        "Maintaining Fitness",
        "You have kept your training load relatively consistent over the "
        "last two weeks, if you want to improve on your current fitness try "
        "and gradually increase your chronic training load.",
    )
    LOSING_FITNESS = (
        "Losing Fitness",
        "Your chronic training load has decreased over the last two weeks, you may "
        "notice a reducing level of fitness as a result.",
    )
    DEFAULT = (
        "Keep Riding",
        "As you complete rides over the coming weeks your daily training load will be calculated "
        "and used to monitor your training progression.",
    )

    @classmethod
    def get_performance_text(cls, current_load, reference_load):
        if not reference_load:
            return cls.DEFAULT.value

        load_change = round(current_load - reference_load, 1)
        if load_change > LOAD_OVERTRAINING_LIMIT:
            return cls.HIGH_RISK_FATIGUE.value
        if load_change > CHRONIC_LOAD_BUFFER:
            return cls.INCREASING_FITNESS.value[0], cls.INCREASING_FITNESS.value[
                1
            ].format(load_change=load_change)
        if load_change > (CHRONIC_LOAD_BUFFER * -1):
            return cls.MAINTAINING_FITNESS.value
        return cls.LOSING_FITNESS.value


class ThresholdPerformanceEnum(Enum):
    NO_DATA_AVAILABLE = (
        "Once you begin uploading ride files with either power or heart rate data your performance "
        "thresholds can be evaluated. When you have completed enough high intensity efforts this "
        "data can be used to estimate your FTP or FTHR. These values will then be used to calculate "
        "your training zones."
    )
    ONLY_POWER_DATA_AVAILABLE = (
        "Based on your uploaded ride data from the last 3 months your estimated FTP is "
        "{overall_max_power_estimate} Watts. The accuracy of this estimated threshold value "
        "is limited by the rides you have uploaded to Pillar. If you have not uploaded any "
        "rides that contained a 'maximum' effort for at least 20 minutes then this will "
        "likely be an underestimate of your true one hour threshold."
    )
    ONLY_HR_DATA_AVAILABLE = (
        "Based on your uploaded ride data from the last 3 months your estimated FTHR is "
        "{overall_max_hr_estimate} beats per minute. The accuracy of this estimated threshold "
        "value is limited by the rides you have uploaded to Pillar. If you have not uploaded "
        "any rides that contained a 'maximum' effort for at least 20 minutes then this will "
        "likely be an underestimate of your true one hour threshold."
    )
    BOTH_POWER_HR_DATA_AVAILABLE = (
        "Based on your uploaded ride data from the last 3 months your estimated FTP is "
        "{overall_max_power_estimate} Watts and your estimated FTHR is "
        "{overall_max_hr_estimate} beats per minute. The accuracy of these estimated "
        "threshold values is limited by the rides you have uploaded to Pillar. If you "
        "have not uploaded any rides that contained a 'maximum' effort for at least 20 "
        "minutes then this will likely be an underestimate of your true one hour threshold."
    )

    @classmethod
    def get_threshold_remarks(
        cls,
        is_power_data_available,
        is_hr_data_available,
        overall_max_power_estimate,
        overall_max_hr_estimate,
    ):

        overall_max_power_estimate = RoundServices.round_power(
            overall_max_power_estimate
        )
        overall_max_hr_estimate = RoundServices.round_heart_rate(
            overall_max_hr_estimate
        )
        if is_power_data_available and is_hr_data_available:
            return cls.BOTH_POWER_HR_DATA_AVAILABLE.value.format(
                overall_max_power_estimate=overall_max_power_estimate,
                overall_max_hr_estimate=overall_max_hr_estimate,
            )
        if is_power_data_available:
            return cls.ONLY_POWER_DATA_AVAILABLE.value.format(
                overall_max_power_estimate=overall_max_power_estimate
            )
        if is_hr_data_available:
            return cls.ONLY_HR_DATA_AVAILABLE.value.format(
                overall_max_hr_estimate=overall_max_hr_estimate
            )
        return cls.NO_DATA_AVAILABLE.value


class FreshnessStateEnum(Enum):
    UNDERTRAINING = "Undertraining"
    RECOVERING = "Recovering"
    BUILDING_FITNESS = "Building Fitness"
    FATIGUED = "Fatigued"
    HIGH_RISK_FATIGUE = "High-Risk Fatigue"

    @classmethod
    def get_freshness_state(cls, freshness_value):
        if freshness_value is None:
            return None
        if freshness_value < -15:
            return cls.HIGH_RISK_FATIGUE.value
        if freshness_value < -10:
            return cls.FATIGUED.value
        if freshness_value < 0:
            return cls.BUILDING_FITNESS.value
        if freshness_value < 5:
            return cls.RECOVERING.value
        return cls.UNDERTRAINING.value


class TimeInZonePerformanceEnum(Enum):
    WEEK_START = (
        "Your focus this week is Zone {current_week_focus}. Click on the More Insight "
        "button below to get an idea of your target time in each intensity zone for "
        "this week and your progress so far. The two zones you have spent the most "
        "time in so far this week are shown below:"
    )
    ZONE_0 = (
        "Your focus for this week is Recovery, so far you have completed "
        "{actual_time_in_zone} minutes of the planned {planned_time_in_zone} minutes "
        "for this week. Remember, it is important you keep your rest weeks easy. The "
        "two zones you have spent the most time in so far this week are shown below:"
    )
    ZONE_1 = (
        "Your focus for this week is Zone 1, so far you have completed "
        "{actual_time_in_zone} minutes of the planned {planned_time_in_zone} minutes "
        "for this week. However, it is important you still maintain some time at "
        "higher intensities. The two zones you have spent the most time in so far this "
        "week are shown below:"
    )
    ZONE_2 = (
        "Your focus for this week is Zone 2, so far you have completed "
        "{actual_time_in_zone} minutes of the planned {planned_time_in_zone} minutes "
        "for this week. However, it is important you still maintain some time at "
        "higher intensities. The two zones you have spent the most time in so far this "
        "week are shown below:"
    )
    ZONE_3 = (
        "Your focus for this week is Zone 3, so far you have completed "
        "{actual_time_in_zone} minutes of the planned {planned_time_in_zone} minutes "
        "for this week. However, it is important that you still maintain some time at "
        "slightly lower intensities. The two zones you have spent the most time in so "
        "far this week are shown below:"
    )
    ZONE_4 = (
        "Your focus for this week is Zone 4, so far you have completed "
        "{actual_time_in_zone} minutes of the planned {planned_time_in_zone} minutes "
        "for this week. However, it is important that you still maintain plenty of "
        "time at  lower intensities. The two zones you have spent the most time in so "
        "far this week are shown below:"
    )
    ZONE_5 = (
        "Your focus for this week is Zone 5, so far you have completed "
        "{actual_time_in_zone} minutes of the planned {planned_time_in_zone} minutes "
        "for this week. However, it is important that you still maintain plenty of "
        "time at lower intensities. The two zones you have spent the most time in so "
        "far this week are shown below:"
    )
    ZONE_6 = (
        "Your focus for this week is Zone 6, so far you have completed "
        "{actual_time_in_zone} minutes of the planned {planned_time_in_zone} minutes "
        "for this week. However, it is important that you still maintain plenty of "
        "time at lower intensities. The two zones you have spent the most time in so "
        "far this week are shown below:"
    )
    ZONE_7 = (
        "Your focus for this week is Zone 7, so far you have completed "
        "{actual_time_in_zone} minutes of the planned {planned_time_in_zone} minutes "
        "for this week. However, it is important that you still maintain plenty of "
        "time at lower intensities. The two zones you have spent the most time in so "
        "far this week are shown below:"
    )

    @classmethod
    def get_time_in_zone_remarks(
        cls,
        current_date,
        current_week_focus,
        actual_time_in_zone,
        planned_time_in_zone,
    ):
        if current_date.weekday() in (0, 1):
            return cls.WEEK_START.value.format(current_week_focus=current_week_focus)

        zone_remarks_texts = {
            0: cls.ZONE_0,
            1: cls.ZONE_1,
            2: cls.ZONE_2,
            3: cls.ZONE_3,
            4: cls.ZONE_4,
            5: cls.ZONE_5,
            6: cls.ZONE_6,
            7: cls.ZONE_7,
        }
        remarks_text = zone_remarks_texts[current_week_focus]

        return remarks_text.value.format(
            actual_time_in_zone=round(actual_time_in_zone / 60),
            planned_time_in_zone=round(planned_time_in_zone / 60),
        )


class ZoneDifficultyLevelPerformanceEnum(Enum):
    DEFAULT = (
        "Your difficulty not increased recently, successfully complete and pair enough sessions with a "
        "zone focus of 3, 4, 5, 6, or 7 to level up the respective zone."
    )
    ZONE_LEVEL_INCREASED = (
        "Nice work, you have increased your difficulty level in Zone {zone_no}! You may now "
        "receive some more challenging sessions with a Zone {zone_no} focus."
    )

    @classmethod
    def get_difficulty_level_remarks(cls, zone_no):
        if zone_no is not None:
            return cls.ZONE_LEVEL_INCREASED.value.format(zone_no=zone_no)
        return cls.DEFAULT.value
