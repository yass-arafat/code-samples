import datetime
import logging

from django.contrib.auth.hashers import check_password
from django.db import models
from django.db.models.query import QuerySet

logger = logging.getLogger(__name__)


class UserQuerySet(QuerySet):
    def get_users(self):
        return self.filter(is_active=True)


class UserAuthModelManager(models.Manager):
    def get_query_set(self):
        return UserQuerySet(self.model)

    def __getattr__(self, attr, *args):
        # see https://code.djangoproject.com/ticket/15062 for details
        if attr.startswith("_"):
            raise AttributeError
        return getattr(self.get_query_set(), attr, *args)

    def get_user(self, code):
        if not code:
            return None
        user = self.filter(code=code, is_active=True).first()

        if not user:
            logger.error(f"No user found with given code {str(code)}.")
            return None

        return user

    def get_refresh_token_bearer_user(self, refresh_token):
        if not refresh_token:
            return None
        user = self.filter(refresh_token=refresh_token, is_active=True).first()

        if not user:
            logger.info(f"No user found with given refresh token {str(refresh_token)}.")
            return None

        return user

    def check_login_credentials(self, email, password):
        user = self.filter(email=email, is_active=True).first()

        if not user:
            logger.info(f"No user found with given email {str(email)}.")
            return False

        return check_password(password, user.password)

    def is_registered(self, email: str):
        try:
            return self.get(email__iexact=email)
        except self.model.DoesNotExist:
            logger.info(f"{email} is not registered yet.")


class OtpManager(models.Manager):
    def smaller_than(self, expiration_time):
        expiration_point = datetime.datetime.now() - datetime.timedelta(
            seconds=expiration_time
        )
        return self.filter(created_at__gte=expiration_point)
