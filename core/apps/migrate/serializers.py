from rest_framework import serializers

from core.apps.achievements.models import PersonalRecord
from core.apps.activities.pillar.models import Activity as PillarData
from core.apps.block.models import UserBlock
from core.apps.challenges.models import Challenge, UserChallenge
from core.apps.daily.models import ActualDay, PlannedDay
from core.apps.garmin.models import CurveCalculationData
from core.apps.packages.models import UserKnowledgeHub
from core.apps.session.models import (
    ActualSession,
    PlannedSession,
    SessionScore,
    UserAway,
    UserAwayInterval,
)
from core.apps.week.models import UserWeek


class MigratePlannedSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlannedSession
        fields = "__all__"


class MigrateUserKnowledgeHubSerializer(serializers.ModelSerializer):
    user_plan_code = serializers.SerializerMethodField()

    class Meta:
        model = UserKnowledgeHub
        fields = ("knowledge_hub", "user_plan_code", "activation_date", "is_active")

    def get_user_plan_code(self, user_knowledge_hub_data):
        return str(user_knowledge_hub_data.user_plan.plan_code)


class MigratePersonalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalRecord
        fields = "__all__"


class MigrateChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = "__all__"


class MigrateUserChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserChallenge
        fields = "__all__"


class MigrateUserAwaySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAway
        fields = "__all__"


class MigrateUserAwayIntervalSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAwayInterval
        fields = "__all__"


class MigratePlannedDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = PlannedDay
        fields = "__all__"


class MigrateUserBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBlock
        fields = "__all__"


class MigrateUserWeekSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserWeek
        fields = "__all__"


class MigratePillarDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PillarData
        fields = "__all__"


class MigrateActualSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActualSession
        fields = "__all__"


class MigrateSessionScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionScore
        fields = "__all__"


class MigrateActualDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = ActualDay
        fields = "__all__"


class MigrateCurveCalculationDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurveCalculationData
        fields = "__all__"
