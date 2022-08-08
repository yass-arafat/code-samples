from django.core.management.base import BaseCommand
from django.utils import timezone

from ...tasks import update_today_focus_message_panel


class Command(BaseCommand):
    help = "Today notification"

    def handle(self, *args, **kwargs):
        time = timezone.now().strftime("%X")
        print("Update today notification for today page started at {0}".format(time))
        update_today_focus_message_panel()
        time = timezone.now().strftime("%X")
        print("Update today notification for today page ended at {0}".format(time))
