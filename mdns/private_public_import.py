from django.core.exceptions import ObjectDoesNotExist

from mdns.zone_migrate import populate_forward_dns, populate_reverse_dns

from dns import zone
from iscpy.iscpy_dns.named_importer_lib import MakeNamedDict
from mozdns.soa.models import SOA
from mozdns.view.models import View

import pdb
import os

# Add zones that should not be imported here
black_list = (
    'svc.mozilla.com',
    'services.mozilla.com',
    )

SYSADMINS_PATH = "/home/juber/sysadmins/"
ZONE_PATH = os.path.join(SYSADMINS_PATH, "dnsconfig")
PRIVATE = os.path.join(SYSADMINS_PATH, "dnsconfig/config/zones.private")
PUBLIC = os.path.join(SYSADMINS_PATH, "dnsconfig/config/zones.public")

def do_import():
    private_zones = MakeNamedDict(open(PRIVATE).read())
    public_zones = MakeNamedDict(open(PUBLIC).read())
    View.objects.get_or_create(name='public')
    View.objects.get_or_create(name='private')
    for zone_name, zone_meta in private_zones['orphan_zones'].iteritems():
        if zone_name in black_list:
            continue
        handle_zone(zone_name, zone_meta, False, True)
    for zone_name, zone_meta in public_zones['orphan_zones'].iteritems():
        if zone_name in black_list:
            continue
        handle_zone(zone_name, zone_meta, True, False)

def get_zone_data(zone_name, filepath, dirpath):
    cwd = os.getcwd()
    os.chdir(dirpath)
    mzone = zone.from_file(filepath, zone_name, relativize=False)
    os.chdir(cwd)
    return mzone


def handle_zone(zone_name, zone_meta, public, private):
    if not zone_meta['file']:
        print "No zone file for {0}".format(zone_name)
        return
    comment = "SOA for " + zone_name
    print "Importing {0}. View: {1}".format(zone_name,
                        'public' if public else 'private')
    mzone = get_zone_data(zone_name, zone_meta['file'], ZONE_PATH)
    views = []
    if public:
        views.append(View.objects.get(name='public'))
    if private:
        views.append(View.objects.get(name='private'))

    if zone_name.endswith(('in-addr.arpa', 'ip6.arpa')):
        direction = 'reverse'
    else:
        direction = 'forward'

    if direction == 'reverse':
        populate_reverse_dns(mzone, zone_name, views)
    else:
        populate_forward_dns(mzone, zone_name, views)
