from django.core.management.base import BaseCommand, CommandError
from mdns.network_build import migrate_networks
import pdb


class Command(BaseCommand):
    args = ''
    help = ''

    def handle(self, *args, **options):
        migrate_networks()
