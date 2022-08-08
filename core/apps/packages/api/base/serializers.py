from rest_framework import serializers

from core.apps.packages.models import Package, SubPackage
from core.apps.plan.utils import is_previous_goal_completed


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = (
            "id",
            "name",
            "title_image_url",
            "purpose",
            "goal_type",
        )


class PackageInfoSerializer(serializers.ModelSerializer):
    previous_goal_completed = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = (
            "id",
            "name",
            "description_image_url",
            "duration",
            "share_link",
            "description",
            "previous_goal_completed",
        )

    def get_previous_goal_completed(self, package):
        return is_previous_goal_completed(self.context["user"])


class SubPackageSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()

    class Meta:
        model = SubPackage
        fields = (
            "id",
            "name",
            "icon_url",
            "purpose",
            "description",
            "duration",
            "multiple_duration",
        )

    def get_duration(self, sub_package):
        if sub_package.duration:
            return f"{round(sub_package.duration / 7)} weeks plan"
