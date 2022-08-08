from django.urls import path

from .views import TrainingBlocksView, get_training_blocks_over_time

urlpatterns = [
    path("get-training-blocks-load/", get_training_blocks_over_time),
    path("training-blocks", TrainingBlocksView.as_view(), name="training-blocks"),
]
