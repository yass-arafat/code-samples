from core.apps.common.tp_common_utils import AliasDict

RECORD_BADGE_URLS = AliasDict(
    {
        "BIGGEST_ELEVATION": "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/achievement/badge/HighestElevation.png",
        "LONGEST_RIDE": "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/achievement/badge/LongestRide.png",
        "FURTHEST_RIDE": "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/achievement/badge/FurthestRide.png",
        "FASTEST_RIDE": "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/achievement/badge/FastestRide.png",
    }
)

RECORD_BADGE_URLS.add_alias("BIGGEST_ELEVATION", 1)
RECORD_BADGE_URLS.add_alias("LONGEST_RIDE", 2)
RECORD_BADGE_URLS.add_alias("FURTHEST_RIDE", 3)
RECORD_BADGE_URLS.add_alias("FASTEST_RIDE", 4)

RECORD_GREY_BADGE_URLS = AliasDict(
    {
        "BIGGEST_ELEVATION_GREY": "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/achievement/badge/HighestElevationGrey.png",
        "LONGEST_RIDE_GREY": "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/achievement/badge/LongestRideGrey.png",
        "FURTHEST_RIDE_GREY": "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/achievement/badge/FurthestRideGrey.png",
        "FASTEST_RIDE_GREY": "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/achievement/badge/FastestRideGrey.png",
    }
)

RECORD_GREY_BADGE_URLS.add_alias("BIGGEST_ELEVATION_GREY", 1)
RECORD_GREY_BADGE_URLS.add_alias("LONGEST_RIDE_GREY", 2)
RECORD_GREY_BADGE_URLS.add_alias("FURTHEST_RIDE_GREY", 3)
RECORD_GREY_BADGE_URLS.add_alias("FASTEST_RIDE_GREY", 4)
