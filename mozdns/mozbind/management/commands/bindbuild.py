from mozdns.mozbind.build import *
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):

    def handle(self, *args, **options):
        build_dns()
