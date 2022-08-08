from core.apps.common.managers import CommonModelManager


class UserPlanManager(CommonModelManager):
    def filter_with_goal(self, **extra_fields):
        return self.filter(**extra_fields).select_related("user_event", "user_package")
