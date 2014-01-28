from systems.models import System, SystemStatus

from core.registration.static.combine_utils import (
    _combine, generate_possible_names, generate_sreg_bundles
)


class BadData(Exception):
    def __init__(self, msg=''):
        self.msg = msg
        return super(BadData, self).__init__()


def decommission_host(hostname, opts):
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
        for sreg in system.staticreg_set.all():
            sreg.decommissioned = True
            sreg.save()
            # This changes things a lot in sreg and will disable hw adapters

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
