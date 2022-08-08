from django.urls import include, path

from core.apps.data_provider.wahoo.api.versioned.v2.urls import private_v2_urlpatterns

urlpatterns = []

private_v2_urlpatterns = [
    path("wahoo/", include(private_v2_urlpatterns)),
]
