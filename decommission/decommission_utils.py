from systems.models import System, SystemStatus

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

    # Attempt to conver the host so an SREG host. This will help with
    # decomming.
    if opts['convert_to_sreg']:
        sreg_convert(system)

    system.system_status = status
    if opts.get('decommission_sreg'):
        bug_number = get_bug_number(comment)
        for sreg in system.staticreg_set.all():
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
