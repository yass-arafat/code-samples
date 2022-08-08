from enum import Enum


class InAppNotificationActionType(Enum):
    INITIATED = 1, "Initiated"
    SHOWED = 2, "Showed"
    CLICKED = 3, "Clicked"
    SWIPED = 4, "Swiped"
    CLOSED = 5, "Closed"


class InAppNotificationClickActionType(Enum):
    ROUTE = 0, "Route"
    URL = 1, "Url"
    APP_UPDATE = 2, "App Update"
    API = 3, "Api Call"


class InAppNotificationButtonType(Enum):
    BAR = "BAR", "Bar"
    REGULAR = "REGULAR", "Regular"
