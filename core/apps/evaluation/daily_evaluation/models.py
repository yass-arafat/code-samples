class DailyTargetPrsObj(object):
    def __init__(self, date, lower_target_prs, upper_target_prs):
        self.date = date
        self.lower_target_prs = round(lower_target_prs)
        self.upper_target_prs = round(upper_target_prs)
