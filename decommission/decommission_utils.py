from systems.models import System, SystemStatus
from mozdns.cname.models import CNAME
from mozdns.srv.models import SRV

from core.registration.static.combine_utils import (
    _combine, generate_possible_names, generate_sreg_bundles
)

import re


class BadData(Exception):
    def __init__(self, msg=''):
        self.msg = msg
        return super(BadData, self).__init__()


def get_bug_number(comment):
    r = re.search('BUG\s*(?P<bug_numbers>(\d+\s*)+)', comment, re.IGNORECASE)
    if r:
        return r.groupdict().get('bug_numbers')
    else:
        return None


def decommission_host(hostname, opts, comment):
    # See https://bugzilla.mozilla.org/show_bug.cgi?id=967082 for what this
    # function should accomplish
    messages = ["Decommission actions for {0}".format(hostname)]
    try:
        system = System.objects.get(hostname=hostname)
    except System.DoesNotExist:
        raise BadData(
            msg="Could not find a system with hostname '{0}'".format(hostname)
        )

    try:
        status = SystemStatus.objects.get(
            status=opts.get('decommission_system_status')
        )
    except SystemStatus.DoesNotExist:
        raise BadData(
            msg="Could not find a system status '{0}'".format(
                opts.get('decommission_system_status')
            )
        )

    # 1) setting the system status to decommissioned
    # 2) deleting any DNS records that are assigned to the host (including
    # CNAME, MX, A, PTR, SRV, etc)
    # 3) deleting any DHCP records that are assigned to the host (but keeping a
    # record of the MACs since that's hardware specific).
    # 4) deleting the operating system
    # 5) deleting allocation (no one owns it anymore and it should not show up
    # in any allocation-based searches).
    # 6) deleting the switch ports and oob switch ports since the machine is no
    # longer hooked up to a switch
    # 7) deleting the oob_ip since the DNS record will no longer exist and this
    # information will be inaccurate
    # 8) deleting the patch panel port (again, it's no longer hooked up to
    # anything)
    # 10) delete information from the k/v store if it exists (pdus, any
    # information related to the panda chassis and imaging servers, etc)

    # Attempt to conver the host so an SREG host. This will help with
    # decomming.
    if opts['convert_to_sreg']:
        sreg_convert(system)

    system.operating_system = None
    system.allocation = None
    system.oob_ip = ''
    system.switch_ports = ''
    system.oob_switch_port = ''
    messages.append(
        "\tCleared values for operating_system, allocation, oob_ip, "
        "switch_ports, and oob_switch_port"
    )

    system.system_status = status
    if opts.get('decommission_sreg'):
        bug_number = get_bug_number(comment)
        for sreg in system.staticreg_set.all():
            if 'DECOMMISSIONED' not in sreg.fqdn:
                messages.append(
                    "\tDeleting: {0}".format(
                        sreg.bind_render_record(reverse=True, rdtype='PTR'))
                )
                messages.append(
                    "\tDeleting: {0}".format(
                        sreg.bind_render_record(rdtype='A'))
                )
            if opts['remove_dns']:
                for cn in CNAME.objects.filter(target=sreg.fqdn):
                    messages.append(
                        "\tDeleting: {0}".format(cn.bind_render_record())
                    )
                    cn.delete()
                for srv in SRV.objects.filter(target=sreg.fqdn):
                    messages.append(
                        "\tDeleting: {0}".format(srv.bind_render_record())
                    )
                    srv.delete()
            sreg.decommissioned = True
            sreg.save()
            # This changes things a lot in sreg and will disable hw adapters
            # At this point the SREG's FQDN will be something like:
            #   [DECOMMISSION] ...
            # If comment has 'BUG \d+' in it, lets put that into the FQDN and
            # resave.
            if bug_number:
                sreg.fqdn = sreg.fqdn.replace(
                    '[DECOMMISSIONED]',
                    '[DECOMMISSIONED BUG {0}]'.format(bug_number)
                )
                sreg.save()

    system.save()  # validation errors caught during unwind
    return messages


def sreg_convert(system):
    bundles = []
    for name in generate_possible_names(system.hostname):
        bundles += generate_sreg_bundles(system, name)

    results = []
    for bundle in bundles:
        results.append(_combine(
            bundle, transaction_managed=True, use_reversion=False
        ))
    return results
