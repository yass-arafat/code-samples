from django.urls import path

from . import views

urlpatterns = [
    path("name/", views.get_name_list_of_named_event),
    path("named-event/<int:event_id>", views.get_named_event),
    # new apis
    path("name/new/", views.NamedEventListView.as_view()),
    path("named-event/<int:event_id>/new/", views.NamedEventDetailView.as_view()),
]
