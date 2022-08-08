import logging

from django.core.management.base import BaseCommand

from ...tasks import run_auto_update

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "run auto update"

    def handle(self, *args, **kwargs):
        run_auto_update()
