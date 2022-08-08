from django.urls import include, path

from core.apps.urls import api_v1_private_urlpatterns as api_private_v1
from core.apps.urls import api_v1_public_urlpatterns as api_public_v1
from core.apps.urls import api_v1_urlpatterns as api_v1
from core.apps.urls import api_v2_private_urlpatterns as api_private_v2
from core.apps.urls import api_v2_urlpatterns as api_v2

urlpatterns = [
    path("v1/", include(api_v1)),
    path("v2/", include(api_v2)),
]

public_urlpatterns = [
    path("v1/", include(api_public_v1)),
    # path("v2/", include(api_public_v1)),
]

private_urlpatterns = [
    path("v1/", include(api_private_v1)),
    path("v2/", include(api_private_v2)),
]
