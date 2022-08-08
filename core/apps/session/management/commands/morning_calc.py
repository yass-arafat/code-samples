from django.core.management.base import BaseCommand
from django.utils import timezone

from ...tasks import morning_calculation


class Command(BaseCommand):
    help = "Morning calculation"

    def handle(self, *args, **kwargs):
        time = timezone.now().strftime("%X")

        print("Morning calculation started at {0}".format(time))
        morning_calculation()
        time = timezone.now().strftime("%X")
        print("Morning calculation ended at {0}".format(time))
