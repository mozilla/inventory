from django.core.management.base import BaseCommand, CommandError
from mdns.dns_build import do_zone_build
import pdb


class Command(BaseCommand):
    args = ''
    help = 'Build dns files: ./manage.py buildzone <zone type> <view> <zone_name> <path-to-zone-file>'

    def handle(self, *args, **options):
        if len(args) != 4:
            print self.help
            return
        do_zone_build(args[0], args[1], args[2], args[3])
        zone_build_from_config()
