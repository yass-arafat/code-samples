import logging

from django.core.management.base import BaseCommand

from ...tasks import generate_week_analysis

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "run auto update"

    def handle(self, *args, **kwargs):
        generate_week_analysis()
