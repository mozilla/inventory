from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.contrib import messages
from django.forms.util import ErrorList
from django.http import HttpResponse

from systems.models import System

from core.interface.static_intr.models import StaticInterface
from core.interface.static_intr.models import StaticIntrKeyValue
from core.interface.static_intr.forms import StaticInterfaceForm
from core.interface.static_intr.forms import FullStaticInterfaceForm
from core.interface.static_intr.forms import StaticInterfaceQuickForm
from core.interface.static_intr.forms import CombineForm
from core.keyvalue.utils import get_attrs, update_attrs, get_aa, get_docstrings
from core.keyvalue.utils import dict_to_kv
from core.range.models import Range
from core.network.utils import calc_parent_str

from mozdns.domain.models import Domain
from mozdns.address_record.models import AddressRecord
from mozdns.ptr.models import PTR

import re
import simplejson as json


def do_combine_a_ptr_to_interface(
        addr, ptr, system, mac_address=None,
        interface=None, dhcp_hostname=None,
        dhcp_domain_name=None, dhcp_domain_name_servers=None,
        dhcp_filename=None):

    if mac_address == '00:00:00:00:00:00' or mac_address is None:
        system.get_next_key_value_adapter()
    if (addr.ip_str != ptr.ip_str or addr.fqdn != ptr.name or
            addr.ip_type != ptr.ip_type):
        raise ValidationError("This A and PTR have different data.")

    intr = StaticInterface(
        label=addr.label, mac=mac_address, domain=addr.domain,
        ip_str=addr.ip_str, ip_type=addr.ip_type, system=system)
    addr_deleted = False
    ptr_deleted = False

    addr.delete(check_cname=False)
    addr_deleted = True
    ptr.delete()
    ptr_deleted = True
    intr.full_clean()
    intr.save()
    if interface:
        from api_v3.system_api import SystemResource
        intr.update_attrs()
        adapter_type, primary, alias = SystemResource.extract_nic_attrs(
            interface)
        intr.attrs.primary = primary
        intr.attrs.alias = alias
        intr.attrs.interface_type = adapter_type
        if dhcp_hostname:
            intr.attrs.hostname = dhcp_hostname

        if dhcp_filename:
            intr.attrs.filename = dhcp_filename

        if dhcp_domain_name:
            intr.attrs.domain_name = dhcp_domain_name

        if dhcp_domain_name_servers:
            intr.attrs.domain_name_servers = dhcp_domain_name_servers

    return intr, addr_deleted, ptr_deleted


def combine_a_ptr_to_interface(request, addr_pk, ptr_pk):
    """
    When a PTR/AddressRecord have the same ip/name it's likely that they could
    become an interface attached to a system. This view (function) takes an
    AddressRecord (addr) and PTR (ptr) and using their data creates an
    StaticInterface. Finally, addr and ptr are deleted.
    """
    addr = get_object_or_404(AddressRecord, pk=addr_pk)
    ptr = get_object_or_404(PTR, pk=ptr_pk)
    is_ajax = request.POST.get('is_ajax')
    system_hostname = request.POST.get('system_hostname')
    if is_ajax and system_hostname:
        system = None
        try:
            system = System.objects.get(hostname=system_hostname)
        except:
            try:
                system_hostname = re.sub('mozilla\.[com|net|org]', '',
                                         system_hostname)
                system = System.objects.get(hostname=system_hostname)
            except:
                system = None
        if system:
            try:
                x = do_combine_a_ptr_to_interface(
                    addr, ptr, system, mac_address="00:00:00:00:00:00")
                (intr, addr_deleted, ptr_deleted) = x
            except ValidationError, e:
                return HttpResponse(json.dumps({'success': False, 'error':
                                                e.messages[0]}))
            ret_dict = {}
            ret_dict['success'] = True
            ret_dict['hostname'] = system.hostname
            ret_dict['id'] = system.id
            return HttpResponse(json.dumps(ret_dict))
        else:
            return HttpResponse(json.dumps({'success': False, 'error':
                                            'Unable to find system'}))

    if request.method == "POST":
        form = CombineForm(request.POST)
        if form.is_valid():
            system = form.cleaned_data['system']
            try:
                x = do_combine_a_ptr_to_interface(addr, ptr, system)
                intr, addr_deleted, ptr_deleted = x
                return redirect(intr)
            except ValidationError, e:
                form.errors['__all__'] = ErrorList(e.messages)
                return render(request, 'static_intr/combine.html', {
                    'addr': addr,
                    'ptr': ptr,
                    'form': form
                })
    else:
        form = CombineForm()
        return render(request, 'static_intr/combine.html', {
            'form': form,
            'addr': addr,
            'ptr': ptr,
        })


def create_no_system_static_interface(request):
    if request.method == "POST":
        interface_form = FullStaticInterfaceForm(request.POST)
        try:
            if not interface_form.is_valid():
                return render(request, 'core/core_form.html', {
                    'form': interface_form,
                })

            intr = interface_form.save()
        except ValidationError, e:
            interface_form._errors['__all__'] = ErrorList(e.messages)
            return render(request, 'core/core_form.html', {
                'form': interface_form,
            })

        return redirect(intr.system.get_absolute_url())

    else:
        initial = {}
        if 'ip_type' in request.GET and 'ip_str' in request.GET:
            ip_str = request.GET['ip_str']
            ip_type = request.GET['ip_type']
            network = calc_parent_str(ip_str, ip_type)
            if network and network.vlan and network.site:
                expected_name = "{0}.{1}.mozilla.com".format(
                    network.vlan.name, network.site.get_site_path())
                try:
                    domain = Domain.objects.get(name=expected_name)
                except ObjectDoesNotExist, e:
                    domain = None

            if domain:
                initial['initial'] = {'ip_str': ip_str, 'domain': domain,
                                      'ip_type': ip_type}
            else:
                initial['initial'] = {'ip_str': ip_str, 'ip_type': ip_type}

        interface_form = FullStaticInterfaceForm(**initial)

        return render(request, 'core/core_form.html', {
            'form': interface_form,
        })


def detail_static_interface(reqeust, intr_pk):
    intr = get_object_or_404(StaticInterface, pk=intr_pk)
    system = intr.system
    return redirect(system)


def delete_static_interface(reqeust, intr_pk):
    intr = get_object_or_404(StaticInterface, pk=intr_pk)
    system = intr.system
    try:
        intr.delete()
    except ValidationError:
        pass
    return redirect(system)


def delete_attr(request, attr_pk):
    """
    An view destined to be called by ajax to remove an attr.
    """
    # system = get_object_or_404(System, pk=system_pk)
    # intr = get_object_or_404(StaticInterface, pk=intr_pk)
    attr = get_object_or_404(StaticIntrKeyValue, pk=attr_pk)
    attr.delete()
    return HttpResponse("Attribute Removed.")


def edit_static_interface(request, intr_pk):
    # TODO, make sure the user has access to this system
    intr = get_object_or_404(StaticInterface, pk=intr_pk)
    system = intr.system
    attrs = intr.staticintrkeyvalue_set.all()
    aa = get_aa(StaticIntrKeyValue())
    docs = get_docstrings(StaticIntrKeyValue())
    if request.method == 'POST':
        interface_form = StaticInterfaceForm(request.POST, instance=intr)
        if interface_form.is_valid():
            try:
                # Handle key value stuff.
                kv = None
                kv = get_attrs(request.POST)
                update_attrs(kv, attrs, StaticIntrKeyValue, intr)
                intr = interface_form.save()

                # Everything checks out. Clean and Save all the objects.
                intr.clean()
                intr.save()
            except ValidationError, e:
                interface_form._errors['__all__'] = ErrorList(e.messages)
                if kv:
                    attrs = dict_to_kv(kv, StaticIntrKeyValue)
                return render(request, 'static_intr/static_intr_edit.html', {
                    'form': interface_form,
                    'intr': intr,
                    'attrs': attrs,
                    'aa': json.dumps(aa),
                    'docs': docs,
                    'form_title': 'Edit Interface for System {0}'.format(
                        system),
                    'domain': intr.domain
                })
        else:
            return render(request, 'static_intr/static_intr_edit.html', {
                'form': interface_form,
                'intr': intr,
                'attrs': attrs,
                'aa': json.dumps(aa),
                'docs': docs,
                'form_title': 'Edit Interface for System {0}'.format(
                    system),
                'domain': intr.domain
            })

        messages.success(request, "Success! Interface Updated.")
        return redirect(intr.get_edit_url())

    else:
        interface_form = StaticInterfaceForm(instance=intr)
        return render(request, 'static_intr/static_intr_edit.html', {
            'form': interface_form,
            'intr': intr,
            'attrs': attrs,
            'aa': json.dumps(aa),
            'docs': docs,
            'form_title': 'Edit Interface for System {0}'.format(system),
            'domain': intr.domain
        })


def create_static_interface(request, system_pk):
    # TODO, make sure the user has access to this system
    system = get_object_or_404(System, pk=system_pk)
    if request.method == 'POST':
        interface_form = StaticInterfaceForm(request.POST)
        interface_form.instance.system = system

        a, ptr, r = None, None, None
        if interface_form.is_valid():
            try:
                intr = interface_form.instance
                intr.system = system
                intr.full_clean()
                intr.save()
            except ValidationError, e:
                interface_form._errors['__all__'] = ErrorList(e.messages)
                return render(request, 'static_intr/static_intr_form.html', {
                    'form': interface_form,
                    'form_title': 'New Interface for System {0}'.format(
                        system)
                })
        else:
            return render(request, 'static_intr/static_intr_form.html', {
                'form': interface_form,
                'form_title': 'New Interface for System {0}'.format(system)
            })

        messages.success(request, "Success! Interface Created.")
        return redirect(system)

    else:
        interface_form = StaticInterfaceForm()
        return render(request, 'static_intr/static_intr_form.html', {
            'form': interface_form,
            'form_title': 'New Interface for System {0}'.format(system)
        })


def quick_create(request, system_pk):
    # TODO, make sure the user has access to this system
    system = get_object_or_404(System, pk=system_pk)
    if request.method == 'POST':
        interface_form = StaticInterfaceQuickForm(request.POST)

        a, ptr, r = None, None, None
        if interface_form.is_valid():
            try:
                # mac = interface_form.cleaned_data['mac']
                if 'label' in interface_form.cleaned_data:
                    label = interface_form.cleaned_data['label']
                else:
                    label = ""
                mrange_pk = interface_form.cleaned_data['range']
                mrange = get_object_or_404(Range, pk=mrange_pk)
                network = mrange.network
                ip_type = network.ip_type
                vlan = network.vlan
                site = network.site

                networks = []
                for network in vlan.network_set.all():
                    if not network.site:
                        continue
                    if network.site.get_site_path() == site.get_site_path():
                        networks.append(network)
                if not networks:
                    raise ValidationError(
                        "No appropriate networks found. Consider adding this "
                        "interface manually.")

                ip = mrange.get_next_ip()
                if ip is None:
                    raise ValidationError(
                        "No appropriate IP found in {0} Vlan {1} Range {2} - "
                        "{3}. Consider adding this interface "
                        "manually.".format(site.name, vlan.name,
                        mrange.start_str, mrange.end_str))

                expected_name = "{0}.{1}.mozilla.com".format(
                    vlan.name, site.get_site_path())
                print "Expected name {0}".format(expected_name)
                try:
                    domain = Domain.objects.get(name=expected_name)
                except ObjectDoesNotExist, e:
                    raise ValidationError(
                        "The domain '{0}' doesn't seem to exist. Consider "
                        "creating this interface manually.".
                        format(expected_name))

                intr = StaticInterface(label=label, domain=domain,
                                       ip_str=str(ip),
                                       # ip_type=ip_type, mac=mac,
                                       # system=system)
                                       ip_type=ip_type, system=system)
                intr.full_clean()
                intr.save()
            except ValidationError, e:
                interface_form._errors['__all__'] = ErrorList(e.messages)
                return render(request, 'static_intr/static_intr_form.html', {
                    'form': interface_form,
                    'form_title': "Quick Interface Create for System "
                    "{0}".format(system)
                })
        else:
            return render(request, 'static_intr/static_intr_form.html', {
                'form': interface_form,
                'form_title': 'Quick Interface Create for System {0}'.format(
                    system)
            })

        messages.success(request, "Success! Interface Created.")
        return redirect(system)

    else:
        interface_form = StaticInterfaceQuickForm()
        return render(request, 'static_intr/static_intr_form.html', {
            'form': interface_form,
            'form_title': 'Quick Interface Create for System {0}'.format(
                system)
        })
