from enum import Enum


class PackageWeekRules(Enum):
    # zone no, session type codes
    ZONE_0 = (0, ("1E", "REST"))
    ZONE_1 = (1, ("1E", "REST"))
    ZONE_2 = (2, ("2E", "1E", "REST"))
    ZONE_3 = (3, ("3K", "1E", "REST"))

    @classmethod
    def get_session_types(cls, zone_focus):
        from core.apps.session.models import SessionType

        for zone_rule in cls:
            if zone_rule.value[0] == zone_focus:
                return SessionType.objects.filter(code__in=zone_rule.value[1]).order_by(
                    "-average_intensity"
                )

        raise ValueError(f"No package rule found for zone focus {zone_focus}")


class HillClimbPackageWeekRules(Enum):
    # zone no, session type codes
    ZONE_0 = (0, ("1E", "REST"))
    ZONE_1 = (1, ("1E", "REST"))
    ZONE_2 = (2, ("2E", "1E", "REST"))
    ZONE_3 = (3, ("3K", "2E", "REST"))
    ZONE_5 = (5, ("5K", "2E", "REST"))
    ZONE_6 = (6, ("6K", "2E", "REST"))
    ZONE_7 = (7, ("7K", "2E", "REST"))
    ZONE_HC = ("HC", ("HC", "2E", "REST"))

    @classmethod
    def get_session_types(cls, zone_focus):
        from core.apps.session.models import SessionType

        for zone_rule in cls:
            if zone_rule.value[0] == zone_focus:
                return SessionType.objects.filter(code__in=zone_rule.value[1]).order_by(
                    "-average_intensity"
                )

        raise ValueError(f"No package rule found for zone focus {zone_focus}")


class PackageDuration(Enum):
    # package duration in weeks, description
    eight_weeks = (
        "8 weeks",
        "Recommended if you have been training regularly over "
        "the past few weeks and also completed a base phase "
        "of training.",
    )
    twelve_weeks = (
        "12 weeks",
        "Recommended if you have been training regularly over" " the past few weeks.",
    )
    sixteen_weeks = (
        "16 weeks",
        "Recommended if you haven't been training regularly "
        "over the past few weeks.",
    )

    @classmethod
    def list(cls):
        duration_list = []
        for member in PackageDuration:
            a = {
                "duration": member.value[0],
                "description": member.value[1],
            }
            duration_list.append(a)
        return duration_list


class GoalTypeEnum(Enum):
    PERFORMANCE = ("PERFORMANCE", "Performance")
    LIFESTYLE = ("LIFESTYLE", "Lifestyle")

    @classmethod
    def get_value(cls, member):
        return cls[member].value[0]


class PackageNameEnum(Enum):
    RETURN_TO_CYCLING = ("RETURN_TO_CYCLING", "Return to Cycling")
    HILL_CLIMB = ("HILL_CLIMB", "Hill Climb")
    WEIGHT_LOSS = ("WEIGHT_LOSS", "Weight Loss")

    @classmethod
    def get_value(cls, member):
        return cls[member].value[1]
