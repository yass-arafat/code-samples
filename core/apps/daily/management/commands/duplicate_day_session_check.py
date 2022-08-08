from django.core.management.base import BaseCommand
from django.utils import timezone

from ...tasks import duplicate_day_session_check


class Command(BaseCommand):
    help = "Duplicate day and session check"

    def handle(self, *args, **kwargs):
        time = timezone.now().strftime("%X")
        print("Duplicate day and session check started at {0}".format(time))

        duplicate_day_session_check()

        time = timezone.now().strftime("%X")
        print("Duplicate day and session check ended at {0}".format(time))
