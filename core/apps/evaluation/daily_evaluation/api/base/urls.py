from django.urls import path

from . import views

urlpatterns = [
    path("get-load-graph/", views.get_planned_load_over_time),
    path("get-seven-days-recovery-graph/", views.get_last_seven_days_recovery_index),
    path("prs-graph", views.prs_graph_view),
    path("sas-graph", views.get_last_seven_days_sas),
    # Depreciated from R8
    path("get-daily-prs/", views.get_daily_prs_over_time),
    path("get-seven-days-sqs-graph/", views.get_last_seven_days_sqs),
]
