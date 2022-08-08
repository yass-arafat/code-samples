class RoundServices:
    @classmethod
    def round_distance(cls, value):
        """Returns distance rounded to 1 decimal place"""
        if value is None:
            return None
        return round(value, 1)

    @classmethod
    def round_speed(cls, value):
        """Returns speed rounded to 1 decimal place"""
        if value is None:
            return None
        return round(value, 1)

    @classmethod
    def round_intensity(cls, value):
        """Returns intensity rounded to 0 decimal place"""
        if value is None:
            return None
        return round(value)

    @classmethod
    def round_power(cls, value):
        """Returns power rounded to 0 decimal place"""
        if value is None:
            return None
        return round(value)

    @classmethod
    def round_weighted_power(cls, value):
        """Returns weighted power rounded to 0 decimal place"""
        if value is None:
            return None
        return round(value)

    @classmethod
    def round_heart_rate(cls, value):
        """Returns heart rate rounded to 0 decimal place"""
        if value is None:
            return None
        return round(value)

    @classmethod
    def round_cadence(cls, value):
        """Returns cadence rounded to 0 decimal place"""
        if value is None:
            return None
        return round(value)

    @classmethod
    def round_elevation(cls, value):
        """Returns elevation rounded to 0 decimal place"""
        if value is None:
            return None
        return round(value)

    @classmethod
    def round_temperature(cls, value):
        """Returns temperature rounded to 0 decimal place"""
        if value is None:
            return None
        return round(value)

    @classmethod
    def round_pss(cls, value):
        """Returns value rounded to 0 decimal place"""
        if value is None:
            return None
        return round(value)

    @classmethod
    def round_sqs(cls, value):
        """Returns SQS rounded to 0 decimal place"""
        if value is None:
            return None
        return round(value)

    @classmethod
    def round_sas(cls, value):
        """Returns SAS rounded to 0 decimal place"""
        if value is None:
            return None
        return round(value)

    @classmethod
    def round_prs(cls, value):
        """Returns PRS rounded to 0 decimal place"""
        if value is None:
            return None
        return round(value)

    @classmethod
    def round_load(cls, value):
        """Returns load rounded to 0 decimal place"""
        if value is None:
            return None
        return round(value)

    @classmethod
    def round_acute_load(cls, value):
        """Returns acute load rounded to 1 decimal place"""
        if value is None:
            return None
        return round(value, 1)

    @classmethod
    def round_recovery_index(cls, value):
        """Returns recovery index rounded to 1 decimal place"""
        if value is None:
            return None
        return round(value, 1)

    @classmethod
    def round_freshness(cls, value):
        """Returns freshness rounded to 0 decimal place"""
        if value is None:
            return None
        return round(value)

    @classmethod
    def round_actual_duration_in_minute(cls, value):
        """Returns actual duration rounded to 0 decimal place"""
        if value is None:
            return None
        return round(value, 1)

    @classmethod
    def round_planned_duration_in_minute(cls, value):
        """Returns planned duration rounded to 0 decimal place"""
        if value is None:
            return None
        return round(value)

    @classmethod
    def round_calories_burnt(cls, value):
        """Returns calories burnt rounded to 0 decimal place"""
        if value is None:
            return None
        return round(value)
