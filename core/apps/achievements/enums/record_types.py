from enum import Enum


class RecordTypes(Enum):
    BIGGEST_ELEVATION = (1, "Biggest Elevation")
    LONGEST_RIDE = (2, "Longest Ride")
    FURTHEST_RIDE = (3, "Furthest Ride")
    FASTEST_RIDE = (4, "Fastest Ride")

    @classmethod
    def ids(cls):
        return [member.value[0] for member in RecordTypes]
