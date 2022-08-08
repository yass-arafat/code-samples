from django.core.management.base import BaseCommand
from django.utils import timezone

from ...tasks import load_sqs_change_check


class Command(BaseCommand):
    help = "Unusual changes in load check"

    def handle(self, *args, **kwargs):
        time = timezone.now().strftime("%X")

        print("Load check started at {0}".format(time))
        load_sqs_change_check.delay()
