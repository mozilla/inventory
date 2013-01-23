from django.core.management.base import BaseCommand
from migrate_dns.private_public_import import do_import


class Command(BaseCommand):
    args = ''
    def handle(self, *args, **options):
        do_import()
