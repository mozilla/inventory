from mozdns.mozbind.build import build_dns
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):
        build_dns()
