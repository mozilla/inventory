import sys
from django.core.management.base import BaseCommand

from migrate_dns.import_utils import show_possible_imports


class Command(BaseCommand):
    args = ''
    def handle(self, *args, **options):
        show_possible_imports(*sys.argv[2:])
