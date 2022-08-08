from enum import Enum

from django.conf import settings


class DaroanURLEnum(Enum):
    REGISTER = settings.DAROAN_URL + "/api/v1/users"  # deprecated in R16
    LOGIN = settings.DAROAN_URL + "/auth/login"  # deprecated in R16
    EMAIL_STATUS = settings.DAROAN_URL + "/auth/email-status"  # deprecated in R16
    RESET_PASSWORD = settings.DAROAN_URL + "/auth/reset-password"
    REFRESH = settings.DAROAN_URL + "/auth/refresh"  # deprecated in R16
    VALIDATE_TOKEN = settings.DAROAN_URL + "/auth/validate-token"

    USER_INFO = settings.DAROAN_URL + "/api/v1/user/info"
    USER_ID = settings.DAROAN_URL + "/api/v1/user"

    # temporary url to move user_auth to Daroan
    MIGRATE_USER = settings.DAROAN_URL + "/api/v1/users/migrate"
    MIGRATE_JOINING_DATE = settings.DAROAN_URL + "/api/v1/users/migrate-joining-date"
