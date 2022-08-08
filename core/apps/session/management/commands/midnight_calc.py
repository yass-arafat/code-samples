from django.core.management.base import BaseCommand
from django.utils import timezone

from ...tasks import midnight_calculation


class Command(BaseCommand):
    help = "Midnight calculation"

    def handle(self, *args, **kwargs):
        time = timezone.now().strftime("%X")

        print("Midnight calculation started at {0}".format(time))
        midnight_calculation()
        time = timezone.now().strftime("%X")
        print("Midnight calculation ended at {0}".format(time))
