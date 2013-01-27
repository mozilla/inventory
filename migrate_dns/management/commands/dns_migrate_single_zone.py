from django.core.management.base import BaseCommand

from migrate_dns.import_utils import migrate_single_zone


class Command(BaseCommand):
    args = ''
    def handle(self, *args, **options):
        migrate_single_zone(args[0], args[1], args[2])
