from enum import Enum


class FeedbackOption(Enum):
    TOO_HARD_INTENSITY = (1, "The intensity was too hard")
    TOO_EASY_INTENSITY = (2, "The intensity was too easy")
    DID_NOT_FUEL_WELL_ENOUGH = (3, "I didn't fuel well enough")
    LOW_SLEEP = (4, "I didn't sleep well")
    DEMOTIVATED = (5, "I am demotivated")
    INJURED = (6, "I am injured")
    TECHNICAL_ISSUE = (7, "I had technical issues")
    OTHER = (8, "Other")

    @classmethod
    def get_feedback_option_code(cls, feedback):
        for x in FeedbackOption:
            if x.value[1].lower() == feedback.lower():
                return x.value[0]
        raise ValueError(f'"{feedback}" does not match with any valid feedback option')

    @classmethod
    def get_feedback_text(cls, code):
        for x in FeedbackOption:
            if x.value[0] == code:
                return x.value[1]
        raise ValueError(f'"{code}" does not match with any valid feedback option code')
