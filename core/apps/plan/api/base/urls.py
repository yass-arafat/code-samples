from django.urls import path

from .views import AsyncMonthPlanView, WeekInfoView

urlpatterns = [
    path(
        "calendar/<int:year>/<int:month>",
        AsyncMonthPlanView.as_view(),
        name="calendar-async",
    ),
    path(
        "calendar/<int:year>/<int:month>/week-info",
        WeekInfoView.as_view(),
        name="week-info",
    ),
]
