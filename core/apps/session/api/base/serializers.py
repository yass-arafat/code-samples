import logging

from rest_framework import serializers

from core.apps.common.common_functions import CommonClass
from core.apps.training_zone.serializers import TrainingZoneSerializer

from ...enums.session_type_enum import SessionTypeEnum
from ...models import PlannedSession, SessionInterval

logger = logging.getLogger(__name__)


class SessionRequestSerializer(serializers.ModelSerializer):
    date = serializers.DateField()

    class Meta:
        model = PlannedSession
        fields = ("date", "block_id")


class SessionResponseSerializer(serializers.ModelSerializer):
    session_type_name = serializers.SerializerMethodField()
    training_zone = serializers.SerializerMethodField()

    class Meta:
        model = PlannedSession
        fields = (
            "id",
            "session_name",
            "session_type_name",
            "goal_hours",
            "session_date_time",
            "status",
            "training_zone",
            "plan",
            "block",
            "week",
        )
        depth = 1

    def get_session_type_name(self, session):
        type_code = session.session_type
        type_name = SessionTypeEnum.get_name(code=type_code)
        return type_name

    def get_training_zone(self, session):
        training_zone = session.zone
        serialize = TrainingZoneSerializer(training_zone)
        return serialize.data


class SessionMonthViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlannedSession
        fields = "__all__"
        depth = 1


class GetSessionIntervalsSerializer(serializers.ModelSerializer):
    description = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    power = serializers.SerializerMethodField()
    hr = serializers.SerializerMethodField()
    cadence = serializers.SerializerMethodField()

    class Meta:
        model = SessionInterval
        fields = ("description", "duration", "power", "hr", "cadence")

    def get_description(self, session_interval):
        return session_interval.name

    def get_duration(self, session_interval):
        is_pad_applicable = self.context["is_pad_applicable"]
        pad_time_in_seconds = self.context["pad_time_in_seconds"]
        if session_interval.is_padding_interval is True and is_pad_applicable is True:
            time_in_seconds = pad_time_in_seconds
        else:
            time_in_seconds = session_interval.time_in_seconds

        return time_in_seconds

    def get_power(self, session_interval):
        cur_ftp = self.context["user_ftp"]
        if not cur_ftp:
            return

        ftp_lower_bound = round((session_interval.ftp_percentage_lower / 100) * cur_ftp)
        ftp_upper_bound = round((session_interval.ftp_percentage_upper / 100) * cur_ftp)
        power = f"{ftp_lower_bound} - {ftp_upper_bound}"
        return power

    def get_hr(self, session_interval):
        if self.context["user_fthr"]:
            return self.get_hr_from_fthr(session_interval)
        return self.get_hr_from_max_hr(session_interval)

    def get_hr_from_fthr(self, session_interval):
        cur_fthr = self.context["user_fthr"]

        fthr_lower_bound = round(
            (session_interval.fthr_percentage_lower / 100) * cur_fthr
        )
        if session_interval.fthr_percentage_upper == 999:
            hr = f">{fthr_lower_bound}"
        else:
            fthr_upper_bound = round(
                (session_interval.fthr_percentage_upper / 100) * cur_fthr
            )
            if session_interval.fthr_percentage_upper == 106:
                hr = f"{fthr_lower_bound} - >{fthr_upper_bound}"
            else:
                hr = f"{fthr_lower_bound} - {fthr_upper_bound}"
        return hr

    def get_hr_from_max_hr(self, session_interval):
        max_hr = self.context["max_hr"]

        mhr_lower_bound = round((session_interval.mhr_percentage_lower / 100) * max_hr)
        if session_interval.mhr_percentage_upper == 999:
            hr = f">{mhr_lower_bound}"
        else:
            mhr_upper_bound = round(
                (session_interval.mhr_percentage_upper / 100) * max_hr
            )
            hr = f"{mhr_lower_bound} - {mhr_upper_bound}"
        return hr

    def get_cadence(self, session_interval):
        avg_cadence = (
            session_interval.cadence_lower + session_interval.cadence_upper
        ) / 2
        return round(avg_cadence)


def get_session_intervals_power_data(cur_ftp, session, is_pad_applicable, time):
    planned_power_data_list = []

    session_intervals = session.session_intervals.order_by("id")

    for interval in session_intervals.iterator():
        if interval.is_padding_interval is True:
            if is_pad_applicable is False:
                continue
            else:
                interval_duration = time
        else:
            interval_duration = interval.time_in_seconds
        power = (
            ((interval.ftp_percentage_lower + interval.ftp_percentage_upper) / 2) / 100
        ) * cur_ftp
        zone_focus = CommonClass.get_zone_focus_from_power(cur_ftp=cur_ftp, power=power)

        for _ in range(int(interval_duration)):
            power_dict = {"value": round(power), "zone_focus": zone_focus}
            planned_power_data_list.append(power_dict)

    return planned_power_data_list


def get_session_intervals_hr_data(cur_fthr, session, is_pad_applicable, time):
    planned_hr_data_list = []

    session_intervals = session.session_intervals.order_by("id")

    for interval in session_intervals.iterator():
        if interval.is_padding_interval is True:
            if is_pad_applicable is False:
                continue
            else:
                interval_duration = time
        else:
            interval_duration = interval.time_in_seconds
        if interval.fthr_percentage_upper == 999:
            hr = (interval.fthr_percentage_lower / 100) * cur_fthr
        else:
            hr = (
                ((interval.fthr_percentage_lower + interval.fthr_percentage_upper) / 2)
                / 100
            ) * cur_fthr
        zone_focus = CommonClass.get_zone_focus_from_hr(cur_fthr=cur_fthr, hr=hr)

        for _ in range(int(interval_duration)):
            hr_dict = {"value": round(hr), "zone_focus": zone_focus}
            planned_hr_data_list.append(hr_dict)

    return planned_hr_data_list
