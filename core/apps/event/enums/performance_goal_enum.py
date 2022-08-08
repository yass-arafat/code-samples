from enum import Enum


class PerformanceGoalEnum(Enum):
    COMPLETE = (1, "Complete")
    COMPETE = (2, "Compete")
    PODIUM = (3, "Podium")

    @classmethod
    def get_value(cls, member):
        return cls[member].value[0]

    @classmethod
    def get_code(cls, performance_goal_text):
        for x in PerformanceGoalEnum:
            if x.value[1] == performance_goal_text:
                return x.value[0]

    @classmethod
    def get_text(cls, performance_goal_code):
        for x in PerformanceGoalEnum:
            if x.value[0] == performance_goal_code:
                return x.value[1]
