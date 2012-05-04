from django.core.management.base import BaseCommand, CommandError
from dns.dns_build import get_dns_data


class Command(BaseCommand):
    args = ''
    help = 'Build dns files'

    def handle(self, *args, **options):
        for ip, macs, hostname in get_dns_data():
            print "IP:{0} Macs: {1} Hostname: {2}".format(ip, macs,
                        hostname)
