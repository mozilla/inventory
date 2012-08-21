from django.core.management.base import BaseCommand, CommandError
from mdns.zone_migrate import buildzone3
import pdb


class Command(BaseCommand):
    args = ''
    def handle(self, *args, **options):
        if len(args) != 1:
            return
        print args
        buildzone3(job=args[0])
