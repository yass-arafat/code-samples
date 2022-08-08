from django.urls import path

from .views import EditGoalApiView

urlpatterns = [
    path("edit-goal", EditGoalApiView.as_view()),
]
