from django.urls import path

from .views import AchievementOverviewView, PersonalRecordView, RecordDetailView

urlpatterns = [
    path("overview", AchievementOverviewView.as_view(), name="achievement-overview"),
    path("record/all", PersonalRecordView.as_view(), name="personal-records"),
    path("record/detail", RecordDetailView.as_view(), name="record-detail"),
]
