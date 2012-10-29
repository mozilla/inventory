from django.core.management.base import BaseCommand, CommandError
from mdns.private_public_import import do_import
import pdb


class Command(BaseCommand):
    args = ''
    def handle(self, *args, **options):
        do_import()
