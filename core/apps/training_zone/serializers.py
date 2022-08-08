from rest_framework import serializers

from .models import TrainingZoneTruthTable


class TrainingZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingZoneTruthTable
        exclude = [
            "is_active",
        ]
