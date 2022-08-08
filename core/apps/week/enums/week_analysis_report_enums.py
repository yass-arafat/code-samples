from enum import Enum


class WeekAnalysisReportTitle(Enum):
    FIRST_WEEK = "The first week of training your {zone_description} completed."
    SECOND_WEEK = "Another week of training your {zone_description} completed."
    THIRD_WEEK = (
        "The final week of training your {zone_description} completed. "
        "Nice! Recovery next week."
    )
    FOURTH_WEEK = "Recovery week complete!"
    DEFAULT = "Week Completed"

    @classmethod
    def get_week_title(
        cls, week_no=None, total_weeks_in_block=None, zone_description=None
    ):
        if week_no is None:
            return cls.DEFAULT.value
        elif week_no == total_weeks_in_block:
            return cls.FOURTH_WEEK.value

        if zone_description is None:
            raise ValueError("User must have zone description for week titles")
        if week_no == total_weeks_in_block - 1:
            title = cls.THIRD_WEEK.value
        elif week_no == 1:
            title = cls.FIRST_WEEK.value
        elif week_no == 2:
            title = cls.SECOND_WEEK.value
        else:
            raise ValueError(f"No week title defined for week no {week_no}")
        return title.format(zone_description=zone_description)


class WeekAnalysisZoneDescription(Enum):
    RECOVERY = (0, "Recovery Week")
    ZONE_1 = (1, "Basic Endurance")
    ZONE_2 = (2, "Endurance")
    ZONE_3 = (3, "Lactate Steady State")
    ZONE_4 = (4, "Maximum Lactate Threshold")
    ZONE_5 = (5, "Maximum Aerobic")
    ZONE_6 = (6, "Anaerobic")
    ZONE_7 = (7, "Neuro Muscular")

    @classmethod
    def get_zone_description(cls, zone_focus):
        for x in cls:
            if zone_focus == x.value[0]:
                return x.value[1]
        raise ValueError(f"{zone_focus} is not a valid zone focus for zone description")


class WeekAnalysisWeekRemarks(Enum):
    NO_PAIRED = (
        "No riding this week? Not able to train due to availability? Injury? "
        "Illness or simply just needed some time off? Let us know if we can help "
        "via the feedback below"
    )
    PSS_RECOVERY = (
        "You did more riding than we planned. Be careful, recovery is where all the "
        "adaptations happen."
    )
    PSS_ZONE1 = (
        "You did more riding than we planned. Be careful, the focus for this blocks "
        "is to get the legs moving and the body use to regular riding."
    )
    RECOVERY_WEEK = (
        "You managed to allow your body to recovery this week. This sets you up nicely "
        "for the next training focus."
    )
    ACHIEVEMENT = (
        "Achievement: you progressed to a more challenging key session. This is all "
        "part of the natural progression. As your body starts to adapt, we need to "
        "provide additional stimulus to encourage the body to adapt further."
    )
    ZONE_DIFFICULTY_LEVEL = (
        "You are progressing with the key sessions for this block. "
        "Keep targeting those rides."
    )
    TIME_IN_ZONE = (
        "You managed to get a good amount of time in the correct zone this week, "
        "great work! (look at the zone distribution below to see how your actual time "
        "compares to your plan for zone {zone_focus})"
    )
    TIME_IN_ZONE_COMPARISON = (
        "You managed to spend less time above zone {zone_focus} this week and "
        "concentrate on your zone {zone_focus}, great!"
    )
    TIME_IN_ZONE_TIPS = (
        "Try to maximise your time in Zone {zone_focus}. Take a look at the zone "
        "distribution chart below. For this block, the aim is to concentrate our "
        "efforts in Zone {zone_focus}. Next week, try to progress more to the planned "
        "time in the zone."
    )
    DURATION_COMPARISON = (
        "You have managed to increase your time riding from {previous_week_duration} "
        "to {duration}."
    )
    TIME_DIFFERENCE_COMPARISON = (
        "You increased your time in the zone by {time_difference} compared to last "
        "week. Great job!"
    )
    SAS = (
        "The quality of your key sessions was great this week. Keep that motivation up "
        "for the coming next week."
    )
    SAS_COMPARISON = (
        "Great, the quality of your key sessions has improved, keep that focus."
    )
    SAS_TIPS = (
        "Really focus on your key session rides for this week.These sessions are "
        "designed to target and stimulate the {zone_description} system.Therefore, "
        "in maximising these sessions, we can expect to see the greatest adaptations "
        "by the end of the block."
    )
    TIME_ABOVE_ZONE_TIPS = (
        "You're spending a lot of time above the target zone focus for this week "
        "({actual_time_above_zone}% of your time this week). This is all good work, "
        "but be cautious as this extra work accounts for more fatigue and therefore "
        "makes it more difficult to maximise your key sessions. Try to spend more time "
        "in zone {zone_focus} and less in the higher zones to get the greatest gains "
        "for this block."
    )
    CADENCE_TIPS = (
        "Try get your cadence up more during your sprints. Power is a function of "
        "force and cadence (revolutions of your legs). So a higher cadence can really "
        "help you improve your sprint. But remember, focus on the technique and don't "
        "force it. It will come"
    )


class WeekAnalysisUTPSummary(Enum):
    TITLE = (
        "We have made some adaption to next weeks training. "
        "The adaptations that we have made are:"
    )
    NO_CHANGE = (
        "We have analysed this week's training and everything looks on track. "
        "There's no need to adapt your plan for next week."
    )


class WeekAnalysisUTPReason(Enum):
    TITLE = "The reasons for these changes are:"
    FIRST_REASON = (
        "You have a worked harder than anticipated this week. We therefore need to "
        "allow you a little less training stress next week to maintain a healthy "
        "balance."
    )
    SECOND_REASON = (
        "We have held back from moving on to more challenging sessions for a bit "
        "longer. We think it would be better to do some extra session at the same "
        "level to really solidify you fitness"
    )
    THIRD_REASON = (
        "We have increased the amount of work to do next week as you appear to be "
        "fresher than we anticipated."
    )
