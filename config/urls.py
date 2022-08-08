from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

from config.api_router import private_urlpatterns as api_private_urlpatterns
from config.api_router import public_urlpatterns as api_public_urlpatterns
from config.api_router import urlpatterns as api_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("public/healthcheck/", include("health_check.urls")),
    path("core-api/public/healthcheck/", include("health_check.urls")),
    path("api/", include(api_urlpatterns)),
    path("public/api/", include(api_public_urlpatterns)),
    path("private/api/", include(api_private_urlpatterns)),
    path("auth-token/", obtain_auth_token),
    path("django-rq/", include("django_rq.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEVELOPMENT in ("dev", "staging"):
    urlpatterns += [path("", include("core.apps.documentation.urls"))]

if settings.DEBUG:
    try:
        import debug_toolbar

        urlpatterns += [
            path("__debug__/", include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass

    if "silk" in settings.INSTALLED_APPS:
        urlpatterns += [url(r"^silk/", include("silk.urls", namespace="silk"))]
