from django.core.management.base import BaseCommand, CommandError
from mdns.dns_build import do_dns_build


class Command(BaseCommand):
    args = ''
    help = 'Build dns files'

    def handle(self, *args, **options):
        do_dns_build()
