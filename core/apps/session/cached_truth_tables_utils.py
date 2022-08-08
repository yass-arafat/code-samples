from django.conf import settings
from django.core.cache import cache

from core.apps.week.models import WeekRules

from .models import Session

check_cache = True


def get_session_types_by_zone_focus(zone_focus):
    cache_key = "zone_focus-" + str(zone_focus)
    if cache_key in cache and check_cache:
        session_types = cache.get(cache_key)
    else:
        session_types = []
        week_rules = WeekRules.objects.filter(zone_focus=zone_focus).order_by(
            "priority_number"
        )
        for week_rule in week_rules:
            session_types.append(week_rule.session_type)
        cache.set(cache_key, session_types, timeout=settings.CACHE_TIME_OUT)
    return session_types


def get_sessions_by_session_type(session_type):
    # cache_key = 'session-type-code-' + str(session_type.code)
    # if cache_key in cache and check_cache:
    #     sessions = cache.get(cache_key)
    # else:
    sessions = (
        session_type.sessions.filter(is_active=True)
        .select_related("session_type")
        .order_by("-pss")
    )
    # cache.set(cache_key, sessions, timeout=settings.CACHE_TIME_OUT)
    return sessions


def get_session_intervals_by_session(session):
    cache_key = "session-code-" + str(session.code)
    if cache_key in cache and check_cache:
        session_intervals = cache.get(cache_key)
    else:
        session_intervals = session.session_intervals.all().order_by("id")
        cache.set(cache_key, session_intervals, timeout=settings.CACHE_TIME_OUT)
    return session_intervals


def get_rest_session():
    cache_key = "REST-SESSION"
    if cache_key in cache and check_cache:
        rest_session = cache.get(cache_key)
    else:
        rest_session = Session.objects.get(code="REST")
        cache.set(cache_key, rest_session, timeout=settings.CACHE_TIME_OUT)
    return rest_session


def get_session_rule_by_session_type(session_type):
    cache_key = "session-type-" + session_type.code + "rule"
    if cache_key in cache and check_cache:
        session_rule = cache.get(cache_key)
    else:
        session_rule = session_type.rule
        cache.set(cache_key, session_rule, timeout=settings.CACHE_TIME_OUT)
    return session_rule


def get_session_type_by_session(session):
    cache_key = "session-type-by-session" + session.code
    if cache_key in cache and check_cache:
        session_type = cache.get(cache_key)
    else:
        session_type = session.session_type
        cache.set(cache_key, session_type, timeout=settings.CACHE_TIME_OUT)
    return session_type
