from django.urls import path

from . import views
from .views import SessionFeedbackView

urlpatterns = [
    path("overview", views.SessionsOverviewViewV2.as_view()),
    path("details", views.SessionDetailView.as_view(), name="session-detail"),
    path("feedback", SessionFeedbackView.as_view(), name="feedback"),
]
