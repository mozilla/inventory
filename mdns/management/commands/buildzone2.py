from django.core.management.base import BaseCommand, CommandError
from mdns.dns_build import zone_build_from_config
import pdb


class Command(BaseCommand):
    args = ''
    def handle(self, *args, **options):
        zone_build_from_config()
