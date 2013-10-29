#  WARNING - This entire file is a temprorary hack that should not be taken
#  srsly.... srsly guise [0]
#
#  This code will go away and was written over 1.5 years ago.... but it still
#  works so its being used.
#
#
#  [0] http://i1339.photobucket.com/albums/o706/schickita/guise_zps0323dbee.jpg

from django.db import transaction
from django.core.exceptions import ValidationError

from systems.models import System, KeyValue as SystemKeyValue

from mozdns.address_record.models import AddressRecord
from mozdns.ptr.models import PTR
from mozdns.view.models import View

from core.registration.static.models import StaticReg
from core.hwadapter.models import HWAdapter, HWAdapterKeyValue
from core.dhcp.render import render_sregs
from core.dhcp.utils import htmlify_dhcp_output

from libs.DHCPHelper import DHCPHelper
from dhcp.DHCP import DHCP as DHCPInterface

import reversion

import pprint
import re

pp = pprint.PrettyPrinter(indent=2)

nic_nums = re.compile("^nic\.(\d+)\..*\.(\d+)$")
is_mac_key = re.compile("^nic\.\d+\.mac_address\.\d+$")
is_hostname_key = re.compile("^nic\.\d+\.hostname\.\d+$")
is_option_hostname_key = re.compile("^nic\.\d+\.option_hostname\.\d+$")
is_ip_key = re.compile("^nic\.\d+\.ipv4_address\.\d+$")
is_dns_auto_build_key = re.compile("^nic\.\d+\.dns_auto_build\.\d+$")
is_dns_auto_hostname_key = re.compile("^nic\.\d+\.dns_auto_hostname\.\d+$")
is_dns_has_conflict_key = re.compile("^nic\.\d+\.dns_has_conflict\.\d+$")
is_name_key = re.compile("^nic\.\d+\.name\.\d+$")
is_some_key = re.compile("^nic\.\d+\.(.*)\.\d+$")


class Interface(object):

    def __init__(self, system, sub_nic):
        self.mac = None
        self.name = ""
        self.hostname = None
        self.option_hostname = ''
        self.nic_ = None
        self.keys = set()
        self.hw_keys = []
        self.obj = system
        self._nic = sub_nic  # Just in case we need it for something
        tmp = nic_nums.match(sub_nic[0].key)
        if tmp:
            self.primary = tmp.group(1)
            self.alias = tmp.group(2)
        else:
            self.primary = None
            self.alias = None
        self.ips = []
        self.dns_auto_build = True
        self.dns_auto_hostname = True
        self.paired = False

    def get_dhcp_output(self):
        kv_ids = map(lambda k: k.pk, self._nic)
        kvs = SystemKeyValue.objects.filter(pk__in=kv_ids)
        return get_old_dhcp_statement(self.obj, kvs)

    def get_html_dhcp_output(self):
        dhcp_output = self.get_dhcp_output()
        if not dhcp_output or not dhcp_output.strip(' \n'):
            return "<span class='no-dhcp-output'>No old DHCP output</span>"
        return htmlify_dhcp_output(dhcp_output, preserve_tabs=True)

    def has_dns_info(self):
        # Eventually do validation here
        if (isinstance(self.ips, list) and len(self.ips) > 0 and
                isinstance(self.hostname, basestring)):
            return True
        else:
            return False

    def set_kv(self, key, value):
        key_str = "nic.{0}.{1}.{2}".format(self.primary, key, self.alias)
        kv = self.obj.keyvalue_set.filter(key=key_str)
        if kv:
            kv = kv[0]
            kv.value = value
            kv.save()
        else:
            kv = System.KeyValue(key=key_str, value=str(value))
            kv.save()

        setattr(self, key, value)
        return

    def delete(self):
        for nic in self._nic:
            nic.delete()

    def emit_hwadapter(self):
        """
        Try to map an Interface's attribtes onto a HW adapter. Also return KV
        pairs.
        """
        return ({
            'mac': self.mac,
            'name': self.name
        }, self.hw_keys)

    def pprint(self):
        return pp.pformat(vars(self))

    def __str__(self):
        return "nic.{0}.{1} IP: {2} Hostname: {3}".format(
            self.primary, self.alias, self.ips, self.hostname
        )

    def __repr__(self):
        return "<Interface: {0}>".format(self)


def build_nics_from_system(system):
    """
    Pass a :class:`System` instance to this function and it will return a list
    of :class:`Interface` objects. Use the interface objects as a proxy for the
    KV store.
    """
    raw_nics = system.keyvalue_set.all()
    formated_nics = transform_nics(raw_nics)
    interfaces = []
    for primary_nic_number, primary_nic in formated_nics.items():
        for sub_nic_number, sub_nic in primary_nic['sub_nics'].items():
            interface = build_nic(sub_nic)
            if not interface:
                continue
            interfaces.append(interface)
    return interfaces


get_nic_primary_number = re.compile("^nic\.(\d+).*$")


def transform_nics(nics):
    """
    Since KV systems have no structure, storing structured data in a KV makes
    extracting data very hard. This function applies a transform to all nics
    linked to a system. It builds a structure that contains all nics in a
    useful format.

    The transform should return something like this::

        {'0': {'sub_nics': {'0': ['nic.0.ipv4_address.0': '192.168.1.1',
                                  'nic.0.mac_address.0': 'DE:AD:BE:EF:00:00'
                                  'nic.0.hostname.0': 'foobar']
                            '1': ['nic.0.ipv4_address.1': '192.168.1.1',
                                  'nic.0.mac_address.1': 'DE:AD:BE:EF:00:00'
                                  'nic.0.hostname.1': 'foobar']}}
         '1': {'sub_nics': {'0': ['nic.1.ipv4_address.0': '192.168.1.1',
                                  'nic.1.mac_address.0': 'DE:AD:BE:EF:00:00'
                                  'nic.1.hostname.0': 'foobar']
                            '1': ['nic.1.ipv4_address.1': '192.168.1.2',
                                  'nic.1.mac_address.1': '11:22:33:44:55:66'
                                  'nic.1.hostname.1': 'bazbar']}}}
    """
    formated_nics = _build_primary_nics(nics)
    for nic_number, nics in formated_nics.items():
        formated_nics[nic_number]['sub_nics'] = _build_sub_nics(nics)
        formated_nics[nic_number].pop('nics')  # We don't need nics anymore.

    return formated_nics


INV_URL = "https://inventory.mozilla.org/en-US/"

INFO = 0
WARNING = 1
ERROR = 2
DEBUG = 3
BUILD = 4


def log(msg, level=0):
    """
    0 - Info
    1 - Warning
    2 - Error
    3 - Debug
    4 - Build
    """
    do_info = True
    do_warning = True
    do_error = True
    do_debug = True
    do_build = True
    if do_info and level == 0:
        print "[INFO] {0}\n".format(msg),
        return
    elif do_warning and level == 1:
        print "[WARNING] {0}\n".format(msg),
        return
    elif do_error and level == 2:
        print "[ERROR] {0}\n".format(msg),
        return
    elif do_debug and level == 3:
        print "[DEBUG] {0}\n".format(msg),
        return
    elif do_build and level == 4:
        print "[BUILD] {0}".format(msg),
        return


def print_system(system):
    return "{0} ({1}systems/edit/{2}/)".format(system, INV_URL, system.pk)


def _build_primary_nics(all_nics):
    """
    Aggregate all nics into their primary groups.
    I.E. All nic\.X.\.*\.Y nics go into a list where all X's are the same.

    :param all_nics: All nics to consider.
    :type all_nics: list
    """
    primary_nics = {}
    for nic in all_nics:
        if not isinstance(nic.key, basestring):
            log("=" * 15, DEBUG)
            log("System {0} and NIC {1} not in valid format.  Value is not "
                "type basestring Skipping.".format(nic.obj, nic), DEBUG)
            log(print_system(nic.obj), DEBUG)
            continue
        possible_primary_nic = get_nic_primary_number.match(nic.key)
        if not possible_primary_nic:
            log("=" * 15, DEBUG)
            log("System {0} and NIC {1} not in valid format. "
                "Skipping.".format(nic.obj, nic), DEBUG)
            log(print_system(nic.obj), DEBUG)
            continue
        primary_nic_number = possible_primary_nic.group(1)
        if primary_nic_number in primary_nics:
            primary_nics[primary_nic_number]['nics'].append(nic)
        else:
            primary_nics[primary_nic_number] = {'nics': [nic]}
    return primary_nics


get_nic_sub_number = re.compile("^nic\.\d+.*\.(\d+)$")


def _build_sub_nics(all_nics):
    """
    Aggregate all sub nics into their sub groups.
    I.E. All nic\.X.\.*\.Y nics go into a list where all Y's are the same.

    :param all_nics: All nics to consider.
    :type all_nics: list
    """
    sub_nics = {}
    for nic in all_nics['nics']:
        possible_sub_nic = get_nic_sub_number.match(nic.key)
        if not possible_sub_nic:
            log("System {0} and NIC {1} not in valid format. "
                "Skipping.".format(nic.obj, nic.key), DEBUG)
            continue
        sub_nic_number = possible_sub_nic.group(1)
        if sub_nic_number in sub_nics:
            sub_nics[sub_nic_number].append(nic)
        else:
            sub_nics[sub_nic_number] = [nic]

    return sub_nics


def build_nic(sub_nic):
    intr = Interface(sub_nic[0].obj, sub_nic)
    for nic_data in sub_nic:
        if is_mac_key.match(nic_data.key):
            if intr.mac is not None:
                log("!" * 20, WARNING)
                log("nic with more than one mac in system {0}"
                    "(https://inventory.mozilla.org/en-US/systems/edit/{1}/"
                    .format(intr.obj, intr.obj.pk), WARNING)
                log(pp.pformat(sub_nic), WARNING)
            intr.mac = nic_data.value
            intr.keys.add('mac')
            continue
        if is_option_hostname_key.match(nic_data.key):
            intr.option_hostname = nic_data.value
            intr.keys.add('option_hostname')
            continue
        if is_name_key.match(nic_data.key):
            intr.name = nic_data.value
            intr.name = intr.name.replace('nic', 'hw')
            intr.keys.add('name')
            continue
        if is_hostname_key.match(nic_data.key):
            if intr.hostname is not None:
                log("!" * 20, WARNING)
                log("nic with more than one hostname in system "
                    "(https://inventory.mozilla.org/en-US/systems/edit/{1}/"
                    .format(intr.obj, intr.obj.pk), WARNING)
                log(pp.pformat(sub_nic), WARNING)
            intr.hostname = nic_data.value
            intr.keys.add('hostname')
            continue
        if is_ip_key.match(nic_data.key):
            intr.ips.append(nic_data.value)
            continue
        if is_dns_auto_build_key.match(nic_data.key):
            if nic_data.value == 'False':
                intr.dns_auto_build = False
            continue
        if is_dns_auto_hostname_key.match(nic_data.key):
            if nic_data.value == 'False':
                intr.dns_auto_hostname = False
            continue
        if is_dns_has_conflict_key.match(nic_data.key):
            if nic_data.value == 'True':
                intr.dns_has_conflict = True
            else:
                intr.dns_has_conflict = False
            continue
        tmp = is_some_key.match(nic_data.key)
        if tmp:
            intr.hw_keys.append({'key': tmp.group(1), 'value': nic_data.value})
            if hasattr(intr, tmp.group(1)):
                setattr(
                    intr, tmp.group(1),
                    [nic_data.value, getattr(intr, tmp.group(1))]
                )
                #intr.keys.add(tmp.group(s))
            else:
                setattr(intr, tmp.group(1), nic_data.value)
    if intr.hostname is None:
        log("System {0} and nic {1}/{2} hast no hostname key, using hostname "
            "found on the system.".format(
            print_system(intr.obj), intr.primary,
            intr.alias), ERROR)
        intr.hostname = intr.obj.hostname

    return intr


def find_matching_a_ptr(name):
    matches = []
    for a in AddressRecord.objects.filter(fqdn=name):
        try:
            ptr = PTR.objects.get(name=a.fqdn, ip_str=a.ip_str)
        except PTR.DoesNotExist:
            continue  # No matching PTR

        views_match = True
        for view in a.views.all():
            if not ptr.views.filter(pk=view.pk):
                views_match = False
                break

        if views_match:
            for view in ptr.views.all():
                if not a.views.filter(pk=view.pk):
                    views_match = False
                    break

        if views_match:
            matches.append((name, a.ip_str, a, ptr))

    return matches


def generate_possible_names(name):
    """
    Its possible for a nic to get a different hostname. This function returns
    some common patterns.
    """
    # releng management host names
    alt_names = [
        "{0}-mgmt.inband.{1}".format(
            name.split('.')[0], '.'.join(name.split('.')[2:])
        ),
        "{0}-mgmt.{1}".format(
            name.split('.')[0], '.'.join(name.split('.')[1:])
        ),
        name
    ]
    return alt_names


def hwadapter_is_for_sreg(match, nic):
    """
    Look at a match and see if the nic should be a HWAdapter attached to it.
    """
    if len(nic.ips) != 1:
        return False

    fqdn, ip_str, _, _ = match

    if not (isinstance(nic.hostname, basestring) or
            isinstance(nic.option_hostname, basestring)):
        return False

    if nic.ips[0] == ip_str and (
            fqdn.startswith(nic.hostname) or
            fqdn.startswith(nic.option_hostname)):
        return True

    return False


def get_all_dhcp_for_system(system, wrap_in_html=True):
    kv_output = get_old_dhcp_statements(system)
    sreg_output = render_sregs(system.staticreg_set.all())
    if not (kv_output.strip(' \n') or sreg_output.strip(' \n')):
        return "<span class='no-dhcp-output'>No old DHCP output</span>"

    if not wrap_in_html:
        return kv_output + '\n\n' + sreg_output

    return (
        htmlify_dhcp_output(kv_output, preserve_tabs=True) +
        htmlify_dhcp_output(sreg_output)
    )


def get_old_dhcp_statements(system):
    return get_old_dhcp_statement(system, system.keyvalue_set)


def get_old_dhcp_statement(system, kvs):
    scope_names = (
        kvs.filter(key__contains='dhcp_scope')
        .values_list('value', flat=True)
        .distinct()
    )
    if not scope_names:
        return ''

    dh = DHCPHelper()
    adapters = []

    for scope in scope_names:
        adapters.append(
            dh.adapters_by_system_and_scope(system, scope)
        )

    adapters[0] = sorted(adapters[0], key=lambda el: el['mac_address'])

    output_text = DHCPInterface([], adapters).get_hosts()
    return output_text


def generate_sreg_bundles(system, name):
    a_ptr_matches = find_matching_a_ptr(name)
    nics = build_nics_from_system(system)
    bundles = {}
    for match in a_ptr_matches:
        fqdn, ip_str, a, ptr = match
        if not nics:
            bundles.setdefault(fqdn + ip_str, {
                'system': system,
                'ptr_pk': ptr.pk,
                'hwadapters': [],
                'fqdn': fqdn,
                'ip': ip_str,
                'a_pk': a.pk,
                'ptr': ptr,
                'a': a
            })
        else:
            for nic in nics:
                if hwadapter_is_for_sreg(match, nic):
                    bundle = bundles.setdefault(fqdn + ip_str, {
                        'system': system,
                        'ptr_pk': ptr.pk,
                        'hwadapters': [],
                        'fqdn': fqdn,
                        'ip': ip_str,
                        'a_pk': a.pk,
                        'ptr': ptr,
                        'a': a
                    })
                    bundle['hwadapters'].append(nic)
                    if nic.paired:
                        print "This nic has already been paired..."
                        import pdb
                        pdb.set_trace()
                    else:
                        nic.paired = True
    pp.pprint(bundles)
    return bundles.values()


@transaction.commit_manually
def combine(bundle, rollback=False, use_reversion=True):
    """
    Returns one sreg and DHCP output for that SREG.

    If rollback is True the sreg will be created and then rolleback, but before
    the rollback all its HWAdapters will be polled for their DHCP output.
    """
    bundle['errors'] = None
    bundle['old-dhcp-output'] = get_all_dhcp_for_system(bundle['system'])
    sreg = StaticReg(
        label=bundle['a'].label, domain=bundle['a'].domain,
        ip_str=bundle['ip'], system=bundle['system'],
        description='Migrated SREG', ip_type=bundle['a'].ip_type
    )

    try:
        bundle['new-dhcp-output'] = (
            "<span class='no-dhcp-output'>No new DHCP output</span>"
        )
        view_names = [v.name for v in bundle['a'].views.all()]
        try:
            bundle['a'].delete(check_cname=False)
        except ValidationError, e:
            rollback = True
            bundle['errors'] = 'Error while deleting the A record.' + str(e)
            return

        try:
            bundle['ptr'].delete()
        except ValidationError, e:
            rollback = True
            bundle['errors'] = 'Error while deleting the PTR record.' + str(e)
            return

        try:
            sreg.save()
            for name in view_names:
                sreg.views.add(View.objects.get(name=name))
            if use_reversion:
                reversion.set_comment('Migrated via combine()')
        except ValidationError, e:
            rollback = True
            bundle['errors'] = 'Error while creating the SREG record.' + str(e)
            return

        for nic in bundle['hwadapters']:
            hw_info, kvs = nic.emit_hwadapter()

            if not hw_info['mac']:
                rollback = True
                return

            try:
                hw, _ = HWAdapter.objects.get_or_create(
                    sreg=sreg, mac=hw_info['mac']
                )
                # HWAdapter class does this for us.
                #hw.name = hw_info['name'].replace
                hw.save()
            except ValidationError, e:
                rollback = True
                bundle['errors'] = 'Error while creating HW Adapter'
                return

            try:
                for kv in kvs:
                    if kv['key'] in ('hostname', 'option_hostname'):
                        # If the option host-name value matches the SREG fqdn
                        # we don't need to add the option, it will be added by
                        # default. all other cases it will be overriden.
                        if kv['value'] == sreg.fqdn:
                            continue
                        else:
                            key = 'host_name'
                    else:
                        key = kv['key']

                    if HWAdapterKeyValue.objects.filter(key=key,
                                                        obj=hw).exists():
                        pass
                    else:
                        kv_ = HWAdapterKeyValue(
                            key=key, value=kv['value'], obj=hw
                        )
                        kv_.clean()
                        kv_.save()
                for kv in nic._nic:
                    SystemKeyValue.objects.filter(pk=kv.pk).delete()
            except ValidationError, e:
                transaction.rollback()
                bundle['errors'] = (
                    'Error while creating HW Adapter KeyValue. ' + str(e)
                )
                return

        bundle['new-dhcp-output'] = get_all_dhcp_for_system(bundle['system'])

        return sreg
    finally:
        if rollback:
            transaction.rollback()
        else:
            transaction.commit()


def combine_multiple(bundles, **kwargs):
    results = []
    for bundle in bundles:
        results.append(combine(bundle, **kwargs))
    return results
