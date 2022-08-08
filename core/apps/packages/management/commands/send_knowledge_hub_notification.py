from django.core.management.base import BaseCommand
from django.utils import timezone

from core.apps.packages.tasks import send_knowledge_hub_tip_notification


class Command(BaseCommand):
    help = "Send weekly knowledge hub notification"

    def handle(self, *args, **kwargs):
        time = timezone.now().strftime("%X")

        print("Send knowledge hub tip notification cron started at {0}".format(time))
        send_knowledge_hub_tip_notification()
        time = timezone.now().strftime("%X")
        print("Send knowledge hub tip notification cron ended at {0}".format(time))
