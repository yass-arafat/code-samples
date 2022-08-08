import logging

logger = logging.getLogger(__name__)


class StravaService:
    @classmethod
    def delete_strava_credentials(cls, user):
        user.strava_user_id = None
        user.strava_user_name = None
        user.strava_user_token = None
        user.strava_refresh_token = None
        user.strava_token_expires_at = None
        try:
            user.save()
            error = False
            msg = "User pillar strava credentials deleted successfully"
        except Exception as e:
            error = True
            msg = f"Couldn't delete user {user.id} pillar strava credentials {str(e)}"

        return error, msg
