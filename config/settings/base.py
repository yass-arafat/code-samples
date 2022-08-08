"""
Base settings to build other settings files upon.
"""
import os
from pathlib import Path

import environ

from . import logger_settings

ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent.parent

# core/
APPS_DIR = ROOT_DIR / "core"
env = environ.Env()

READ_DOT_ENV_FILE = env.bool("DJANGO_READ_DOT_ENV_FILE", default=False)

if READ_DOT_ENV_FILE:
    # OS environment variables take precedence over variables from .env
    env.read_env(str(ROOT_DIR / ".env"))

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool("DJANGO_DEBUG", False)

DEVELOPMENT = env("DEVELOPMENT")

# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

TIME_ZONE = "UTC"
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "en-us"
# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
# https://docs.djangoproject.com/en/dev/ref/settings/#locale-paths
LOCALE_PATHS = [str(ROOT_DIR / "locale")]

# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASE_SCHEMA_NAME = "public"

# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = "config.urls"
# https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = "config.wsgi.application"

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    # TODO remove this sites app with migration
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "django.forms",
]

THIRD_PARTY_APPS = [
    "crispy_forms",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
]

THIRD_PARTY_APPS += [
    "drf_yasg",
    "rest_framework_swagger",
    "clear_cache",
    "ckeditor",
    "django_rq",
    "imagekit",
    "scheduler",
    "push_notifications",
    "health_check",
    "health_check.db",
    # 'health_check.contrib.rabbitmq',
    "health_check.contrib.redis",
]

LOCAL_APPS = [
    "core.apps.documentation.apps.DocumentationConfig",
    "core.apps.user_auth.apps.UserAuthConfig",
    "core.apps.user_profile.apps.UserProfileConfig",
    "core.apps.plan.apps.PlanConfig",
    "core.apps.block.apps.BlockConfig",
    "core.apps.week.apps.WeekConfig",
    "core.apps.garmin.apps.GarminConfig",
    "core.apps.session.apps.SessionConfig",
    "core.apps.settings.apps.SettingsConfig",
    "core.apps.common.apps.CommonConfig",
    "core.apps.training_zone.apps.TrainingZoneConfig",
    "core.apps.event.apps.EventConfig",
    "core.apps.daily.apps.DailyConfig",
    "core.apps.evaluation.session_evaluation",
    "core.apps.evaluation.daily_evaluation",
    "core.apps.evaluation.block_evaluation",
    "core.apps.evaluation.goal",
    "core.apps.utp.apps.UtpConfig",
    "core.apps.notification.apps.NotificationConfig",
    "core.apps.cms.apps.CmsConfig",
    "core.apps.strava.apps.StravaConfig",
    "core.apps.etp.apps.EtpConfig",
    "core.apps.athlete.apps.AthleteConfig",
    "core.apps.activities.apps.ActivitiesConfig",
    "core.apps.activities.pillar",
    "core.apps.performance.apps.PerformanceConfig",
    "core.apps.achievements.apps.AchievementsConfig",
    "core.apps.authorization.apps.AuthorizationConfig",
    "core.apps.challenges.apps.ChallengesConfig",
    "core.apps.home.apps.HomeConfig",
    "core.apps.packages.apps.PackagesConfig",
    "core.apps.subscription.apps.SubscriptionConfig",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIGRATIONS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#migration-modules
MIGRATION_MODULES = {"sites": "core.contrib.sites.migrations"}

# Log Configuration
LOGGING = logger_settings.LOGGING

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.common.BrokenLinkEmailsMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.apps.user_auth.middleware.UserAuthenticationMiddleware",
    "log_request_id.middleware.RequestIDMiddleware",
]

# STATIC
# ------------------------------------------------------------------------------
STATIC_ROOT = str(ROOT_DIR / "staticfiles")  # noqa F405
STATICFILES_DIRS = [str(APPS_DIR / "static")]
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(APPS_DIR / "media")
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/media/"

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        "DIRS": [str(APPS_DIR / "templates")],
        "OPTIONS": {
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "core.utils.context_processors.settings_context",
            ],
        },
    }
]

# https://docs.djangoproject.com/en/dev/ref/settings/#form-renderer
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

# http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = "bootstrap4"

# FIXTURES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#fixture-dirs
FIXTURE_DIRS = (str(APPS_DIR / "fixtures"),)

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-browser-xss-filter
SECURE_BROWSER_XSS_FILTER = True
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = "DENY"

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
)
# https://docs.djangoproject.com/en/dev/ref/settings/#email-timeout
EMAIL_TIMEOUT = 5

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = "/admin/"
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = [("""Daniel Wakerley""", "daniel-wakerley@example.com")]
# https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

# django-allauth
# ------------------------------------------------------------------------------
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_EMAIL_VERIFICATION = "mandatory"

# django-rest-framework
# -------------------------------------------------------------------------------
# django-rest-framework - https://www.django-rest-framework.org/api-guide/settings/
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
    "COERCE_DECIMAL_TO_STRING": False,  # it will not convert decimal values to string
}

# django-cors-headers - https://github.com/adamchainz/django-cors-headers#setup
CORS_URLS_REGEX = r"^/api/.*$"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__ + "/../")))

API_SECRET_KEY = env("API_SECRET_KEY")

# Garmin
GARMIN_CONSUMER_KEY = env("GARMIN_CONSUMER_KEY")
GARMIN_CONSUMER_SECRET = env("GARMIN_CONSUMER_SECRET")

# Strava
STRAVA_CLIENT_ID = env("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = env("STRAVA_CLIENT_SECRET")

# Dakghor Microservice Config
DAKGHOR_API_SECRET_KEY = env("DAKGHOR_API_SECRET_KEY")
DAKGHOR_URL = env("DAKGHOR_URL")

# Daroan Microservice Config
DAROAN_API_SECRET_KEY = env("DAROAN_API_SECRET_KEY")
DAROAN_URL = env("DAROAN_URL")
TREASURY_URL = env("TREASURY_URL")

# Trainer Microservice Config
TRAINER_API_SECRET_KEY = env("TRAINER_API_SECRET_KEY")
TRAINER_URL = env("TRAINER_URL")

# Email Microservice Secret Key
EMAIL_MICROSERVICE_SECRET_KEY = env("EMAIL_MICROSERVICE_SECRET_KEY")
EMAIL_MS_BASE_URL = env("EMAIL_MS_BASE_URL")
DEFAULT_EMAIL = env("DEFAULT_EMAIL")

EMAIL_USE_TLS = True
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_PORT = 587

EMAIL_NOTIFICATION_RECEPIENT_LIST = env.list("EMAIL_NOTIFICATION_RECEPIENT_LIST")
CRON_EMAIL_SENDER = env("CRON_EMAIL_SENDER")
OTP_EMAIL_SENDER = env("OTP_EMAIL_SENDER")
USER_SUPPORT_EMAIL_SENDER = env("USER_SUPPORT_EMAIL_SENDER")
CRON_USER_NAME = env("CRON_USER_NAME")

ASYNC_HEALTHCHECK_URL = env("ASYNC_HEALTHCHECK_URL")

RQ_QUEUES = {
    "default": {
        "HOST": env("RQ_DEFAULT_URL"),
        "PORT": env("RQ_DEFAULT_PORT"),
        "DB": 0,
        # 'PASSWORD': 'some-password',
        "DEFAULT_TIMEOUT": env("RQ_DEFAULT_TIMEOUT"),
    },
    "high": {
        "HOST": env("RQ_DEFAULT_URL"),
        "PORT": env("RQ_DEFAULT_PORT"),
        # 'DB': env('RQ_DEFAULT_DB'),
        "DB": 0,
        # 'PASSWORD': 'some-password',
        "DEFAULT_TIMEOUT": env("RQ_DEFAULT_TIMEOUT"),
    },
    "low": {
        "HOST": env("RQ_DEFAULT_URL"),
        "PORT": env("RQ_DEFAULT_PORT"),
        # 'DB': env('RQ_DEFAULT_DB'),
        "DB": 0,
        # 'PASSWORD': 'some-password',
        "DEFAULT_TIMEOUT": env("RQ_DEFAULT_TIMEOUT"),
    },
}

CACHE_TIME_OUT = 60 * 60 * 3

AWS_PRIVATE_MEDIA_LOCATION = "media"
PRIVATE_FILE_STORAGE = "config.storage_backends.PublicMediaStorage"

#  imagekit related settings
IMAGEKIT_CACHEFILE_DIR = "CACHE/images"
IMAGEKIT_CACHEFILE_NAMER = "imagekit.cachefiles.namers.hash"
IMAGEKIT_CACHE_BACKEND = "default"
IMAGEKIT_CACHE_PREFIX = "imagekit:"
IMAGEKIT_CACHE_TIMEOUT = 300
IMAGEKIT_DEFAULT_CACHEFILE_BACKEND = "imagekit.cachefiles.backends.Simple"
IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY = "imagekit.cachefiles.strategies.JustInTime"
IMAGEKIT_DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
IMAGEKIT_SPEC_CACHEFILE_NAMER = "imagekit.cachefiles.namers.source_name_as_path"
IMAGEKIT_USE_MEMCACHED_SAFE_CACHE_KEY = True

OTP_RESEND_MINIMUM_TIME = 60
OTP_EXPIRATION_TIME = 300  # seconds
OTP_ACCESS_TOKEN_EXPIRATION_TIME = 600  # seconds

PUSH_NOTIFICATIONS_SETTINGS = {
    "FCM_API_KEY": env("FCM_API_KEY"),
    "UPDATE_ON_DUPLICATE_REG_ID": True,
    "UNIQUE_REG_ID": True,
    "USER_MODEL": "user_auth.UserAuthModel",
}

# TODO need to check and discuss why this two needed
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
# healthcheck api related settings
BROKER_URL = env("CELERY_BROKER_URL")  # this is needed for the healthcheck api to run
REDIS_URL = env("REDIS_URL")

# hubspot disable and enable
HUBSPOT_ENABLE = env.bool("HUBSPOT_ENABLE")

GENERATE_REQUEST_ID_IF_NOT_IN_HEADER = True
LOG_REQUEST_ID_HEADER = "HTTP_CORRELATION_ID"
REQUEST_ID_RESPONSE_HEADER = "HTTP_CORRELATION_ID"
