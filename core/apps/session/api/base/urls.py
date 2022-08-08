# api/v1/session/
from django.urls import path

from . import views

urlpatterns = [
    path("change-status/", views.change_session_status),
    path("move/", views.move_session),
    path("delete/", views.delete_session),
    path("user/away", views.UserAwayApiView.as_view()),
    path("user/away/delete", views.UserAwayDeleteApiView.as_view()),
    path("user/away/delete/all", views.UserAwayDeleteAllApiView.as_view()),
    path("pair", views.SessionPairingView.as_view(), name="session-pairing"),
    path("unpair", views.SessionUnpairingView.as_view(), name="session-unpairing"),
    path(
        "message/dismiss",
        views.CancelPairingMessageView.as_view(),
        name="cancel-pairing-message",
    ),
    path("delete", views.SessionDeleteView.as_view(), name="session-delete"),
    path("edit", views.SessionEditView.as_view(), name="session-edit"),
    path("warning", views.SessionWarningView.as_view(), name="session-warning"),
    path(
        "warning/dismiss",
        views.SessionWarningDismissView.as_view(),
        name="warning-dismiss",
    ),
]
