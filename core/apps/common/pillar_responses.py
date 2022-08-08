from rest_framework.response import Response

from core.apps.user_profile.models import UserActivityLog


class PillarResponse(Response):
    """
    This response class overrides DRF response and writes
    user activity log if needed.
    """

    def __init__(
        self,
        user=None,
        user_id=None,
        request=None,
        data=None,
        activity_code=None,
        status=None,
        template_name=None,
        headers=None,
        exception=False,
        content_type=None,
    ):
        super().__init__(data, status, template_name, headers, exception, content_type)
        if activity_code:
            self.log_activity(user_id, request, data, activity_code)

    def log_activity(self, user_id, request, response, activity_code):
        UserActivityLog.objects.create(
            user_id=user_id,
            request=request.data,
            response=response,
            activity_code=activity_code,
        )
