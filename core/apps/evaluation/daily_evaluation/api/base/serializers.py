from datetime import datetime
from decimal import Decimal

from rest_framework import serializers

from core.apps.common.date_time_utils import DateTimeUtils
from core.apps.daily.models import ActualDay, PlannedDay

from ...models import DailyTargetPrsObj


class ActualDayPrsSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()

    class Meta:
        model = ActualDay
        fields = ("date", "value")

    def get_date(self, actual_day):
        offset = self.context["offset"]
        return DateTimeUtils.get_user_local_date_from_utc(
            offset, datetime.combine(actual_day.activity_date, datetime.min.time())
        )

    def get_value(self, actual_day):
        if actual_day.prs_score < 0.0:
            return 0.0
        return round(actual_day.prs_score)


class ActualDayPrsAccuracySerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()

    class Meta:
        model = ActualDay
        fields = ("date", "value")

    def get_date(self, actual_day):
        offset = self.context["offset"]
        return DateTimeUtils.get_user_local_date_from_utc(
            offset, datetime.combine(actual_day.activity_date, datetime.min.time())
        )

    def get_value(self, actual_day):
        return round(max(actual_day.prs_accuracy_score, Decimal(0)))


class PlannedDayLoadSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()

    class Meta:
        model = PlannedDay
        fields = ("date", "value")

    def get_date(self, planned_day):
        offset = self.context["offset"]
        return DateTimeUtils.get_user_local_date_from_utc(
            offset, datetime.combine(planned_day.activity_date, datetime.min.time())
        )

    def get_value(self, planned_day):
        return planned_day.planned_load


class UserLastSevenDaysRISerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()

    class Meta:
        model = ActualDay
        fields = ("date", "value")

    def get_date(self, actual_day):
        offset = self.context["offset"]
        return DateTimeUtils.get_user_local_date_from_utc(
            offset, datetime.combine(actual_day.activity_date, datetime.min.time())
        )

    def get_value(self, actual_day):
        return actual_day.recovery_index


class UserLastSevenDaysSQSSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()

    class Meta:
        model = ActualDay
        fields = ("date", "value")

    def get_date(self, actual_day):
        offset = self.context["offset"]
        return DateTimeUtils.get_user_local_date_from_utc(
            offset, datetime.combine(actual_day.activity_date, datetime.min.time())
        )

    def get_value(self, actual_day):
        return actual_day.sqs_today


class UserLastSevenDaysSASSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()

    class Meta:
        model = ActualDay
        fields = ("date", "value")

    def get_date(self, actual_day):
        offset = self.context["offset"]
        return DateTimeUtils.get_user_local_date_from_utc(
            offset, datetime.combine(actual_day.activity_date, datetime.min.time())
        )

    def get_value(self, actual_day):
        return actual_day.sas_today


class DailyTargetPrsObjSerializer(serializers.Serializer):
    date = serializers.DateField()
    lower_target_prs = serializers.IntegerField()
    upper_target_prs = serializers.IntegerField()

    class Meta:
        model = DailyTargetPrsObj
        fields = "__all__"
