from core.apps.common.const import MTP_OVER_TRAINING_INTENSITY as MTI


class SessionEditOptions:
    def __init__(self, user, current_week, today):
        self.user = user
        self.user_current_week = current_week
        self.local_today = today
        self.current_week_days = self.get_current_week_days()
        self.current_week_planned_sessions = self.get_current_week_planned_sessions()
        self.current_week_actual_sessions = self.get_current_week_actual_sessions()
        self.current_week_actual_session_codes = list(
            self.current_week_actual_sessions.values_list("session_code", flat=True)
        )
        self.current_week_session_intensities = (
            self.calculate_week_days_session_intensities()
        )

    def get_current_week_days(self):
        away_dates_flat_list = list(
            self.user.user_away_days.filter(is_active=True).values_list(
                "away_date", flat=True
            )
        )
        days = (
            self.user.planned_days.filter(
                week_code=self.user_current_week.week_code, is_active=True
            )
            .exclude(activity_date__in=away_dates_flat_list)
            .order_by("activity_date")
        )
        return days

    def get_current_week_planned_sessions(self):
        start_date = self.user_current_week.start_date
        end_date = self.user_current_week.end_date
        planned_sessions = (
            self.user.planned_sessions.filter(
                is_active=True,
                session_date_time__gte=start_date,
                session_date_time__lte=end_date,
            )
            .order_by("session_date_time")
            .values(
                "session_code", "zone_focus", "session_date_time", "planned_intensity"
            )
        )
        planned_sessions_dict = {}
        for session in planned_sessions:
            planned_sessions_dict[session["session_date_time"].date()] = session

        return planned_sessions_dict

    def get_current_week_actual_sessions(self):
        planned_session_codes = []
        for key, session in self.current_week_planned_sessions.items():
            planned_session_codes.append(str(session["session_code"]))
        session_codes = [str(code) for code in planned_session_codes]
        actual_sessions = self.user.actual_sessions.filter(
            is_active=True, session_code__in=session_codes
        ).order_by("session_date_time")
        return actual_sessions

    def calculate_week_days_session_intensities(self):
        intensities = [0] * 7
        for key, session in self.current_week_planned_sessions.items():
            intensities[session["session_date_time"].weekday()] = session[
                "planned_intensity"
            ]

        for session in list(
            self.current_week_actual_sessions.values_list(
                "actual_intensity", "session_date_time"
            )
        ):
            intensities[session[1].weekday()] = session[0]
        intensities = [float(intensity) for intensity in intensities]
        return intensities

    def get_session(self, planned_sessions, day, today):
        session = planned_sessions.filter(day_code=day.day_code).first()
        if session:
            if (
                day.activity_date < today and not session.is_completed
            ):  # if past day session is not completed then it is a rest day
                return None
            else:
                return session
        else:
            return None

    def check_high_intensity(self, data_list, parameter):
        return all(i > parameter for i in data_list)

    def check_over_training(self, day, moving_session_date_time):
        consecutive_days = False
        high_intensity = False
        day_no = day.activity_date.weekday()

        # high intensity condition
        new_intensity_list = self.current_week_session_intensities.copy()
        new_intensity_list[day_no] = self.current_week_session_intensities[
            moving_session_date_time.weekday()
        ]
        high_intensity_case1 = self.check_high_intensity(
            new_intensity_list[max(0, day_no - 2) : day_no + 1], MTI
        )
        high_intensity_case2 = self.check_high_intensity(
            new_intensity_list[max(0, day_no - 1) : day_no + 2], MTI
        )
        high_intensity_case3 = self.check_high_intensity(
            new_intensity_list[max(0, day_no) : day_no + 3], MTI
        )

        if high_intensity_case1 or high_intensity_case2 or high_intensity_case3:
            high_intensity = True

        # recovery day condition
        consecutive_days_case1 = self.check_high_intensity(
            new_intensity_list[max(0, day_no - 3) : day_no + 1], 0
        )
        consecutive_days_case2 = self.check_high_intensity(
            new_intensity_list[max(0, day_no - 2) : day_no + 2], 0
        )
        consecutive_days_case3 = self.check_high_intensity(
            new_intensity_list[max(0, day_no - 1) : day_no + 3], 0
        )
        consecutive_days_case4 = self.check_high_intensity(
            new_intensity_list[max(0, day_no) : day_no + 4], 0
        )

        if (
            consecutive_days_case1
            or consecutive_days_case2
            or consecutive_days_case3
            or consecutive_days_case4
        ):
            consecutive_days = True

        if consecutive_days:
            return "RECOVERY"
        elif high_intensity:
            return "HIGH_INTENSITY"
        else:
            return None

    def get_movable_days(self, moving_session_date_time):
        movable_days = []
        local_today_no = self.local_today.weekday()
        possible_movable_days = self.current_week_days[local_today_no:]
        for day in possible_movable_days:
            if self.current_week_planned_sessions[day.activity_date]["zone_focus"] == 0:
                over_training_message = self.check_over_training(
                    day, moving_session_date_time
                )
                movable_days.append(
                    {
                        "day_id": day.id,
                        "date": day.activity_date,
                        "day_name": day.activity_date.strftime("%A"),
                        "over_training": over_training_message,
                    }
                )
        return movable_days

    def session_completed(self, session_code):
        return session_code in self.current_week_actual_session_codes

    def check_cancellable(
        self, session_zone_focus, session_date_time, session_completed
    ):
        today = self.local_today
        week = self.user_current_week
        if (
            session_zone_focus != 0
            and session_completed is False
            and (today <= session_date_time.date() <= week.end_date)
        ):
            return True
        else:
            return False

    def check_movable(self, session_zone_focus, session_date_time, session_completed):
        week = self.user_current_week
        if (
            session_zone_focus != 0
            and session_completed is False
            and (week.start_date <= session_date_time.date() <= week.end_date)
        ):
            return True
        else:
            return False

    def get_session_edit_options(self):
        edit_options = []
        for day in self.current_week_days:
            session_value = self.current_week_planned_sessions[day.activity_date]
            movable_days = []
            session_completed = self.session_completed(session_value["session_code"])
            session_is_cancellable = self.check_cancellable(
                session_value["zone_focus"],
                session_value["session_date_time"],
                session_completed,
            )
            session_is_movable = self.check_movable(
                session_value["zone_focus"],
                session_value["session_date_time"],
                session_completed,
            )
            if session_is_movable:
                movable_days = self.get_movable_days(session_value["session_date_time"])
            edit_options.append(
                self.make_dict_from_data(
                    day.activity_date,
                    session_is_cancellable,
                    session_is_movable,
                    movable_days,
                )
            )

        return edit_options

    def make_dict_from_data(
        self, date, session_is_cancellable, session_is_movable, movable_days
    ):
        return {
            "date": date,
            "session_edit_options": {
                "is_cancellable": session_is_cancellable,
                "is_movable": session_is_movable,
                "movable_days": movable_days,
            },
        }
