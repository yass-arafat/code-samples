from django.urls import include, path

from ...pillar.api.base.urls import urlpatterns as api_pillar

urlpatterns = [path("pillar/", include(api_pillar))]
