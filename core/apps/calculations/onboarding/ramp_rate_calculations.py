import calendar

calendar.setfirstweekday(calendar.MONDAY)


def get_fraction_of_ramp_rate(week_day):
    return (7 - week_day) / 7


def get_calculated_ramp_rate(date, ramp_rate):
    return round((get_fraction_of_ramp_rate(date.weekday()) * ramp_rate), 2)
