from django.urls import path

from . import views

urlpatterns = [
    path("get-session-evaluation-details/", views.get_session_details_data),
    path(
        "session-evaluation-details",
        views.SessionEvaluationDetailsView.as_view(),
        name="session-details",
    ),
    path("get-session-evaluation-graph/", views.get_session_graph_data_with_threshold),
    path(
        "session-evaluation-graph",
        views.SessionGraphDataView.as_view(),
        name="session-evaluation-graph",
    ),
]
