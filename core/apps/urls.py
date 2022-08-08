from django.urls import include, path

from .achievements.api.versioned.v2.urls import urlpatterns as api_achievements_v2
from .activities.api.base.urls import urlpatterns as api_activity
from .athlete.api.base.urls import urlpatterns as api_athletes
from .challenges.api.base.urls import urlpatterns as api_challenges_v1
from .cms.api.base.urls import private_v1_urlpatterns as api_private_v1_cms
from .daily.api.base.urls import urlpatterns as api_daily
from .data_provider.urls import private_v2_urlpatterns as api_data_provider_v2
from .etp.api.base.urls import urlpatterns as api_etp
from .evaluation.urls import urlpatterns as api_evaluations
from .evaluation.urls import urlpatterns_v2 as api_evaluations_v2
from .event.api.base.urls import urlpatterns as api_events
from .garmin.api.base.urls import private_v1_urlpatterns as api_private_v1_garmin
from .home.api.versioned.v2.urls import urlpatterns as api_home_v2
from .migrate.api.base.urls import private_v1_urlpatterns as migrate_urlpatterns
from .notification.api.base.urls import private_v1_sync_urlpatterns
from .notification.api.base.urls import private_v1_urlpatterns as api_notification_v1
from .notification.api.base.urls import (
    private_v1_urlpatterns as api_private_v1_notification,
)
from .notification.api.base.urls import urlpatterns as api_notification
from .packages.api.base.urls import urlpatterns as api_packages
from .performance.api.versioned.v2.urls import urlpatterns as api_performance_v2
from .plan.api.base.urls import urlpatterns as api_plan
from .plan.api.versioned.v2.urls import urlpatterns as api_plan_v2
from .session.api.base.urls import urlpatterns as api_session
from .session.api.versioned.v2.urls import urlpatterns as api_session_v2
from .settings.api.versioned.v2.urls import urlpatterns as api_settings_v2
from .strava.api.base.urls import private_v1_urlpatterns as api_private_v1_strava
from .subscription.api.base.urls import urlpatterns as api_subscription
from .training_zone.api.versioned.v2.urls import urlpatterns as api_training_zone_v2
from .user_auth.api.base.urls import public_urlpatterns as public_api_user_auth
from .user_auth.api.base.urls import urlpatterns as api_user_auth
from .user_profile.api.base.urls import (
    private_v1_urlpatterns as api_v1_private_user_profile,
)
from .user_profile.api.base.urls import v1_urlpatterns as api_user_profile_v1
from .user_profile.api.versioned.v2.urls import url_patterns as api_user_profile_v2
from .user_profile.api.versioned.v2.urls import (
    url_patterns_private_v2 as api_user_profile_private_v2,
)
from .week.api.versioned.v2.urls import urlpatterns as api_week_v2

api_v1_urlpatterns = [
    path("activity/", include(api_activity)),
    path("auth/", include(api_user_auth)),
    path("user/", include(api_user_profile_v1)),
    # path("users/", include(api_user_profile_v1)),
    path("athlete/", include(api_athletes)),
    path("plan/", include(api_plan)),
    path("session/", include(api_session)),
    path("day/", include(api_daily)),
    path("event/", include(api_events)),
    path("evaluation/", include(api_evaluations)),
    path("notifications", include(api_notification)),
    path("notifications/", include(api_notification)),
    path("sync/", include(api_notification)),
    path("etp/", include(api_etp)),
    path("challenges/", include(api_challenges_v1)),
    path("packages/", include(api_packages)),
    path("subscription/", include(api_subscription)),
]

api_v2_urlpatterns = [
    path("user/", include(api_user_profile_v2)),
    path("plan/", include(api_plan_v2)),
    path("session/", include(api_session_v2)),
    path("sessions/", include(api_session_v2)),
    path("evaluation/", include(api_evaluations_v2)),
    path("performance/", include(api_performance_v2)),
    path("training-zones", include(api_training_zone_v2)),
    path("achievement/", include(api_achievements_v2)),
    path("home/", include(api_home_v2)),
    path("week/", include(api_week_v2)),
    path("data-provider/", include(api_data_provider_v2)),
    path("settings/", include(api_settings_v2)),
]

api_v1_public_urlpatterns = [
    path("auth/", include(public_api_user_auth)),
]

api_v1_private_urlpatterns = [
    path("user/", include(api_v1_private_user_profile)),
    path("cms/", include(api_private_v1_cms)),
    path("garmin/", include(api_private_v1_garmin)),
    path("strava/", include(api_private_v1_strava)),
    path("notification/", include(api_private_v1_notification)),
    # TODO Remove it when every user moves to > R16.2
    path("sync/", include(private_v1_sync_urlpatterns)),
    path("migrate/", include(migrate_urlpatterns)),
]

api_v2_private_urlpatterns = [
    path("user/", include(api_user_profile_private_v2)),
    path("notifications/", include(api_notification_v1)),
]
