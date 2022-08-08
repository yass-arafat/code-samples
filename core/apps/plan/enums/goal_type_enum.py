from enum import Enum


class GoalTypeEnum(str, Enum):
    EVENT = "EVENT"
    PACKAGE = "PACKAGE"

    @classmethod
    def lower(cls):
        lower = {s.lower() for s in cls.__members__}
        return lower

    @classmethod
    def goal_type_of_plan(cls, user_plan):
        if user_plan.user_event_id:
            return cls.EVENT.value
        if user_plan.user_package_id:
            return cls.PACKAGE.value
        raise ValueError("User plan has no goal")
