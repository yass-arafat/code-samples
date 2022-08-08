from django.urls import path

from .views import TodayDetailsView, get_today_details_data

urlpatterns = [
    path("get-today-details/", get_today_details_data),
    path("today/details", TodayDetailsView.as_view(), name="today-details"),
]
