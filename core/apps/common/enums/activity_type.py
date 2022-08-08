import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ActivityTypeEnum(Enum):
    """
    Here first one denotes code, second one denotes the type and 3rd one is for the message text.
    Yo can change the 3rd one as per the product requirement any time
    """

    UNDEFINED = (-1, "undefined", "Undefined")
    DEFAULT = (0, "activity", "Activity")
    GENERIC = (1, "generic", "Generic")
    RUNNING = (2, "running", "Run")
    CYCLING = (3, "cycling", "Ride")
    GYM_FITNESS_EQUIPMENT_OR_BREATHWORK = (4, "training", "Training")
    HIKING = (5, "hiking", "Hiking")
    SWIMMING = (6, "swimming", "Swim")
    WALKING = (7, "walking", "Walk")
    TRANSITION = (8, "transition", "Transition")
    MOTORCYCLING = (9, "motorcycling", "MotorCycle")
    OTHER = (10, "generic", "Generic")
    AUTO_RACING = (11, "auto_racing", "Auto Race")
    BOATING = (12, "boating", "Boat")
    DRIVING = (14, "driving", "Driving")
    FLOOR_CLIMBING = (15, "floor_climbing", "Floor Climbing")
    GOLF = (16, "golf", "Golf")
    HANG_GLIDING = (17, "hang_gliding", "Hand Gliding")
    HORSEBACK_RIDING = (18, "horseback_riding", "Horseback Ride")
    HUNTING_FISHING = (19, "fishing", "Fishing")
    INLINE_SKATING = (20, "inline_skating", "Inline Skating")
    MOUNTAINEERING = (21, "mountaineering", "Mountaineering")
    OFFSHORE_OR_ONSHORE_GRINDING = (
        22,
        "offshore_or_onshore_grinding",
        "Offshore or Onshore Grinding",
    )
    PADDLING = (23, "paddling", "Paddling")
    RC_DRONE_OR_WINGSUIT_OR_FLYING = (24, "flying", "Flying")
    ROCK_CLIMBING = (25, "rock_climbing", "Rock Climbing")
    ROWING = (26, "rowing", "Rowing")
    SAILING = (27, "sailing", "Sailing")
    SKY_DIVING = (28, "sky_diving", "Sky diving")
    STAND_UP_PADDLEBOARDING = (
        29,
        "stand_up_paddleboarding",
        "Stand Up Paddle boarding",
    )
    STOPWATCH = (30, "stopwatch", "Stopwatch")
    SURFING = (31, "surfing", "Surfing")
    TENNIS = (32, "tennis", "Tennis")
    WAKEBOARDING = (33, "water_skiing", "Water Skiing")
    WHITEWATER_KAYAKING_RAFTING = (34, "kayaking", "Kayaking")
    WIND_KITE_SURFING = (35, "windsurfing", "Windsurfing")
    DIVING = (36, "diving", "Diving")
    WINTER_SPORTS = (37, "winter_sports", "Winter Sports")
    BACKCOUNTRY_SKIING_OR_RESORT_SKIING_OR_SNOWBOARDING = (
        38,
        "alpine_skiing",
        "Alpine Skiing",
    )
    CROSS_COUNTRY_CLASSIC_OR_SKATE_SKIING = (
        39,
        "cross_country_skiing",
        "Cross Country Skiing",
    )
    SKATING = (40, "ice_skating", "Ice skating")
    SNOWSHOEING = (41, "snowshoeing", "Snowshoeing")
    SNOWMOBILING = (42, "snowmobiling", "Snowmobiling")

    @classmethod
    def get_value(cls, member):
        return cls[member].value[0]

    @classmethod
    def get_text_from_code(cls, code):
        for x in ActivityTypeEnum:
            if x.value[0] == code:
                return x.value[1]
        raise ValueError("{} is not a valid Enum code".format(code))

    @classmethod
    def get_code_from_text(cls, text):
        for x in ActivityTypeEnum:
            if x.value[1] == text:
                return x.value[0]
        raise ValueError("{} is not a valid Enum text".format(text))

    @classmethod
    def get_pillar_defined_activity_name(cls, activity_type):
        # declaring Set instead of lists as searching in set is O(1)
        cycling_keys = {"cycling", "ride", "ebikeride", "virtualride"}
        if activity_type.lower() in cycling_keys:
            return cls.CYCLING.value[1]

        running_keys = {"running", "run", "virtualrun"}
        if activity_type.lower() in running_keys:
            return cls.RUNNING.value[1]

        return None

    @classmethod
    def is_pillar_supported(cls, activity_type: str):
        accepted_types = (
            ActivityTypeEnum.CYCLING.value[1],
            ActivityTypeEnum.RUNNING.value[1],
        )
        return bool(activity_type and activity_type.lower() in accepted_types)

    @classmethod
    def get_pillar_defined_message_text(cls, activity_type: str):
        # TODO: Apply best practise
        if activity_type is None:
            return ActivityTypeEnum.DEFAULT.value[2]

        if activity_type.lower() == ActivityTypeEnum.RUNNING.value[1].lower():
            return ActivityTypeEnum.RUNNING.value[2]
        elif activity_type.lower() == ActivityTypeEnum.CYCLING.value[1].lower():
            return ActivityTypeEnum.CYCLING.value[2]
        else:
            logger.error(
                f"Unsupported activity type used for message text. Type: {activity_type}"
            )
            return ActivityTypeEnum.DEFAULT.value[2]
