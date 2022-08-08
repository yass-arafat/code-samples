from django.urls import path, re_path

from . import views

urlpatterns = [
    # Registration API path
    # path("register/", views.UserRegisterView.as_view()),
    re_path(r"^activate/$", views.UserRegisterView.activate, name="activate"),
    # Login
    # path("login/", views.UserLoginView.as_view()),
    # path("new/login/", views.LoginView.as_view()),
    # path("garmin/de-registration/", views.user_garmin_deregistration),
    # path("garmin/", views.user_garmin_login),
    # Refresh access token
    # path("renew-access-token/", views.RenewAccessTokenView.as_view()),
    # Status check
    # path("email/status/", views.EmailStatusView.as_view()),
    # Logout
    # path("logout/", csrf_exempt(views.UserLogOutView.as_view())),
]

public_urlpatterns = [
    path("reset-password", views.UserPasswordResetApiView.as_view()),
    path("otp-request", views.OtpRequestApiView.as_view()),
    path("otp-verify", views.OtpVerificationApiView.as_view()),
]
