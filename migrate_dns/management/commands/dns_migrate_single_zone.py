from django.core.management.base import BaseCommand

from migrate_dns.import_utils import migrate_single_zone
from mozdns.view.models import View


class Command(BaseCommand):
    args = ''
    def handle(self, *args, **options):
        View.objects.get_or_create(name='public')
        View.objects.get_or_create(name='private')
        migrate_single_zone(args[0], args[1], args[2])
