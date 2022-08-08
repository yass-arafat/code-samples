from django.urls import include, path

urlpatterns = [
    path("day/", include("core.apps.evaluation.daily_evaluation.api.base.urls")),
    path("block/", include("core.apps.evaluation.block_evaluation.api.base.urls")),
    path("session/", include("core.apps.evaluation.session_evaluation.api.base.urls")),
    # Should be removed
    path("daily/", include("core.apps.evaluation.daily_evaluation.api.base.urls")),
]

urlpatterns_v2 = [
    path("goal/", include("core.apps.evaluation.goal.api.versioned.v2.urls"))
]
