from django.core.management.base import BaseCommand, CommandError
from core.search.compiler import invparse

class Command(BaseCommand):
    def handle(self, *args, **options):
        pass
