from datetime import datetime, timedelta

from django.db.models import Q

from core.apps.common.date_time_utils import DateTimeUtils
from core.apps.session.models import PlannedSession, UserAwayInterval

from ..event.services import get_user_event_dates
from ..packages.models import UserKnowledgeHub
from .api.base.serializers import (
    ActualSessionSerializer,
    AwayTileSerializerClass,
    PlannedSessionCustomSerializer,
)
from .dictionary import get_week_focus_dictionary


class SessionDetailsForMonth:
    def __init__(
        self, user, calendar_start_date, calendar_end_date, pro_feature_access
    ):
        self.user = user
        self.start_date = calendar_start_date
        self.end_date = calendar_end_date
        self.month_plan_dict = []
        self.user_profile_data = user.profile_data.filter(is_active=True).last()
        self.timezone_offset = self.user.timezone_offset
        self.user_away_dates = list(
            self.user.user_away_days.filter(is_active=True).values_list(
                "away_date", flat=True
            )
        )
        self.completed_days = self.get_completed_days_by_date()
        self.user_events = self.user.user_events.filter(is_active=True)
        self.event_dates = (
            get_user_event_dates(user_events=self.user_events)
            if self.user_events
            else []
        )
        self.pro_feature_access = pro_feature_access

    def is_day_completed(self, date):
        if date in self.completed_days:
            return True
        return False

    def get_completed_days_by_date(self):
        negative_time_zone_user = True if self.timezone_offset[0] == "-" else False
        query_start_date = (
            self.start_date + timedelta(days=1)
            if negative_time_zone_user
            else self.start_date
        )
        query_end_date = (
            self.end_date + timedelta(days=1)
            if negative_time_zone_user
            else self.end_date
        )
        completed_days = self.user.actual_sessions.filter(
            session_date_time__range=(query_start_date, query_end_date),
            session_code__isnull=False,
            is_active=True,
        ).values_list("session_date_time__date", flat=True)
        return list(completed_days)

    def get_event_dates(self):
        event_dates = []
        event_start_dates = list(self.user_events.values_list("start_date", flat=True))
        event_end_dates = list(self.user_events.values_list("end_date", flat=True))

        event_dates_length = len(event_start_dates)
        for index in range(event_dates_length):
            current_date = event_start_dates[index]
            while current_date <= event_end_dates[index]:
                event_dates.append(current_date)
                current_date += timedelta(days=1)

        return event_dates

    def get_serialized_planned_sessions(self):
        if not self.pro_feature_access:
            return {}

        query_dict = {
            "session_date_time__range": (self.start_date, self.end_date),
            "is_active": True,
        }
        planned_sessions = (
            self.user.planned_sessions.filter(**query_dict)
            .exclude(session_date_time__in=self.user_away_dates)
            .select_related("session")
            .order_by("session_date_time")
        )

        serialized_planned_sessions = PlannedSessionCustomSerializer(
            planned_sessions, self.event_dates, self.user, self.user_events
        )
        data = serialized_planned_sessions.data
        return data

    def get_serialized_actual_sessions(self):
        negative_time_zone_user = True if self.timezone_offset[0] == "-" else False
        query_start_date = (
            self.start_date + timedelta(days=1)
            if negative_time_zone_user
            else self.start_date
        )
        query_end_date = (
            self.end_date + timedelta(days=1)
            if negative_time_zone_user
            else self.end_date
        )

        query_dict = {
            "session_date_time__date__range": (query_start_date, query_end_date),
            "is_active": True,
            "third_party__isnull": False,
        }
        actual_sessions = (
            self.user.actual_sessions.filter_actual_sessions(user_auth=self.user)
            .filter(**query_dict)
            .order_by("session_date_time")
            .select_related("third_party")
        )
        if self.pro_feature_access:
            actual_sessions.exclude(session_date_time__date__in=self.user_away_dates)

        planned_sessions = self.user.planned_sessions.filter(
            session_date_time__range=(self.start_date, self.end_date), is_active=True
        ).exclude(session_date_time__in=self.user_away_dates)
        context = {
            "event_dates": self.event_dates,
            "planned_sessions": planned_sessions,
            "actual_sessions": actual_sessions.values("session_code", "third_party"),
            "pro_feature_access": self.pro_feature_access,
            "user_away": False,
        }
        serialized_actual_sessions = ActualSessionSerializer(
            actual_sessions, context=context, many=True
        )
        data = serialized_actual_sessions.data
        return data

    def merge_planned_and_actual_sessions(
        self, planned_sessions_data, actual_sessions_data
    ):
        day_sessions = {}
        for planned_session in planned_sessions_data:
            session_date = planned_session["session_date_time"].date()
            day_sessions[session_date] = [planned_session]

        for actual_session in actual_sessions_data:
            session_date = actual_session["session_date_time"].date()

            # if unplanned session then just add this session for that day
            if session_date not in day_sessions:
                day_sessions[session_date] = [actual_session]
                continue
            # if unpaired session then just add this session to that day_sessions list
            if actual_session["session_code"] is None:
                day_sessions[session_date].append(actual_session)
                continue

            # if session has session code but no third party (recovery session), skip it
            if (
                actual_session["session_code"]
                and not actual_session["third_party_code"]
            ):
                continue
            # if paired session then replace planned session with actual session
            if actual_session["session_code"] and actual_session["third_party_code"]:
                day_sessions[session_date][0] = actual_session
        return day_sessions

    def day_details_for_month(self):
        negative_time_zone_user = True if self.timezone_offset[0] == "-" else False
        query_start_date = (
            self.start_date + timedelta(days=1)
            if negative_time_zone_user
            else self.start_date
        )
        query_end_date = (
            self.end_date + timedelta(days=1)
            if negative_time_zone_user
            else self.end_date
        )
        query_dict = {
            "activity_date__range": (query_start_date, query_end_date),
            "is_active": True,
        }
        zone_focus_by_date = dict(
            list(
                self.user.planned_days.filter(**query_dict)
                .order_by("activity_date")
                .exclude(activity_date__in=self.user_away_dates)
                .values_list("activity_date", "zone_focus")
            )
        )

        planned_sessions_data = self.get_serialized_planned_sessions()
        actual_sessions_data = self.get_serialized_actual_sessions()

        month_sessions = self.merge_planned_and_actual_sessions(
            planned_sessions_data, actual_sessions_data
        )

        for _date, sessions in month_sessions.items():
            zone_focus = zone_focus_by_date.get(_date, None)
            self.month_plan_dict.append(
                {
                    "date": _date,
                    "zone_focus": zone_focus,
                    "is_planned_day": type(zone_focus) is int,
                    "is_completed": self.is_day_completed(_date),
                    "week_focus": {},
                    "day_sessions": sessions,
                    "knowledge_hub": self.get_knowledge_hub_data(_date),
                }
            )
        return self.month_plan_dict

    def get_knowledge_hub_data(self, date):
        current_date = DateTimeUtils.get_user_local_date_from_utc(
            self.timezone_offset, datetime.now() - timedelta(minutes=6)
        )
        user_knowledge_hub = UserKnowledgeHub.objects.filter(
            activation_date=date, is_active=True, user_id=self.user.code
        ).last()
        if date > current_date or not user_knowledge_hub:
            return {"id": None, "text": None}
        knowledge_hub = user_knowledge_hub.knowledge_hub
        return {"id": knowledge_hub.id, "text": knowledge_hub.calendar_text}


class DailyWeekFocusForMonth:
    def __init__(
        self, user, calendar_start_date, calendar_end_date, pro_feature_access
    ):
        self.user = user
        self.start_date = calendar_start_date
        self.end_date = calendar_end_date
        self.week_focus_list = []
        self.weeks_cache = {}
        self.user_plans_cache = {}
        self.total_blocks_cache = {}
        self.user_block_cache = {}
        self.initialize_weeks()
        self.pro_feature_access = pro_feature_access

    def initialize_weeks(self):
        weeks = self.user.user_weeks.filter(
            Q(start_date__range=(self.start_date, self.end_date))
            | Q(end_date__range=(self.start_date, self.end_date)),
            is_active=True,
        )
        for week in weeks:
            self.weeks_cache[week.week_code] = week

    def week_focus_for_month(self):
        if not self.pro_feature_access:
            return self.week_focus_list

        query_dict = {
            "activity_date__range": (self.start_date, self.end_date),
            "is_active": True,
        }
        planned_days = self.user.planned_days.filter(**query_dict).order_by(
            "activity_date"
        )
        for day in planned_days:
            week = self.weeks_cache[day.week_code]
            if week.block_code in self.user_plans_cache:
                user_plan = self.user_plans_cache[week.block_code]
            else:
                user_block = self.user.user_blocks.filter(
                    block_code=week.block_code, is_active=True
                ).last()
                user_plan = self.user.user_plans.filter(
                    plan_code=user_block.plan_code, is_active=True
                ).last()
                self.user_plans_cache[week.block_code] = user_plan
                self.user_block_cache[week.block_code] = user_block

            current_block = self.user_block_cache[week.block_code]

            if user_plan.plan_code in self.total_blocks_cache:
                total_blocks = self.total_blocks_cache[user_plan.plan_code]
            else:
                total_blocks = self.user.user_blocks.filter(
                    plan_code=user_plan.plan_code, is_active=True
                ).count()
                self.total_blocks_cache[user_plan.plan_code] = total_blocks

            week_focus = get_week_focus_dictionary(
                self.user, week, total_blocks, current_block
            )
            self.week_focus_list.append(
                {
                    "date": day.activity_date,
                    "week_focus": week_focus,
                }
            )

        return self.week_focus_list


class UserAwayTilesForMonth:
    def __init__(
        self, user, calendar_start_date, calendar_end_date, pro_feature_access
    ):
        self.user = user
        self.start_date = calendar_start_date
        self.end_date = calendar_end_date
        self.timezone_offset = self.user.timezone_offset
        self.away_tiles_list = []
        self.user_profile_data = user.profile_data.filter(is_active=True).last()

        self.away_interval_cache = {}
        self.pro_feature_access = pro_feature_access

    def get_serialized_actual_sessions(self, away_dates):
        query_dict = {
            "session_date_time__date__in": away_dates,
            "is_active": True,
            "third_party__isnull": False,
        }
        actual_sessions = self.user.actual_sessions.filter(**query_dict).select_related(
            "third_party"
        )
        context = {
            "planned_sessions": PlannedSession.objects.none(),
            "pro_feature_access": self.pro_feature_access,
            "user_away": True,
        }
        serialized_actual_sessions = ActualSessionSerializer(
            actual_sessions, context=context, many=True
        )
        actual_sessions_data = serialized_actual_sessions.data
        day_sessions = {}
        for actual_session in actual_sessions_data:
            session_date = actual_session["session_date_time"].date()
            if session_date not in day_sessions:
                day_sessions[session_date] = [actual_session]
            else:
                day_sessions[session_date].append(actual_session)
        return day_sessions

    def away_tiles_for_month(self):
        if not self.pro_feature_access:
            return self.away_tiles_list

        negative_time_zone_user = True if self.timezone_offset[0] == "-" else False
        query_start_date = (
            self.start_date + timedelta(days=1)
            if negative_time_zone_user
            else self.start_date
        )
        query_end_date = (
            self.end_date + timedelta(days=1)
            if negative_time_zone_user
            else self.end_date
        )
        query_dict = {
            "away_date__range": (query_start_date, query_end_date),
            "is_active": True,
        }
        user_away_days = self.user.user_away_days.filter(**query_dict)
        away_dates = list(user_away_days.values_list("away_date", flat=True))
        actual_sessions_data = self.get_serialized_actual_sessions(away_dates)
        for away_day in user_away_days:
            if away_day.interval_code in self.away_interval_cache:
                away_interval = self.away_interval_cache[away_day.interval_code]
            else:
                away_interval = UserAwayInterval.objects.filter(
                    interval_code=away_day.interval_code, is_active=True
                ).first()

            serialized_away_tile = AwayTileSerializerClass(
                self.user, away_day, away_interval
            )

            actual_sessions = []
            if away_day.away_date in actual_sessions_data:
                actual_sessions = actual_sessions_data[away_day.away_date]

            self.away_tiles_list.append(
                {
                    "date": DateTimeUtils.get_user_local_date_from_utc(
                        self.timezone_offset,
                        datetime.combine(away_day.away_date, datetime.min.time()),
                    ),
                    "zone_focus": None,
                    "is_completed": False,
                    "week_focus": {},
                    "day_sessions": [serialized_away_tile.get_data()] + actual_sessions,
                }
            )

        return self.away_tiles_list


def merge_data(result):
    session_data_len = len(result["session_data"])
    for edit_option in result["edit_option_data"]:
        _date = edit_option["date"]

        for i in range(session_data_len):
            if result["session_data"][i]["date"] == _date:
                session_len = len(result["session_data"][i]["day_sessions"])
                for j in range(session_len):
                    if not result["session_data"][i]["day_sessions"][j][
                        "session_metadata"
                    ]["planned_id"]:
                        continue
                    if (
                        result["session_data"][i]["day_sessions"][j][
                            "session_date_time"
                        ].date()
                        == _date
                    ):
                        result["session_data"][i]["day_sessions"][j][
                            "session_edit_options"
                        ] = edit_option["session_edit_options"]

    week_focus_len = len(result["week_focus_data"])
    session_index = 0
    away_index = 0

    total_sessions = len(result["session_data"])

    for i in range(week_focus_len):
        if (
            session_index < total_sessions
            and result["session_data"][session_index]["date"]
            == result["week_focus_data"][i]["date"]
        ):
            result["session_data"][session_index]["week_focus"] = result[
                "week_focus_data"
            ][i]["week_focus"]
            session_index += 1
        else:
            result["away_tiles_data"][away_index]["week_focus"] = result[
                "week_focus_data"
            ][i]["week_focus"]
            away_index += 1

    return result["session_data"] + result["away_tiles_data"]
