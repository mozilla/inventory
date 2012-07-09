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
from core.interface.static_intr.forms import StaticInterfaceQuickForm
from core.keyvalue.utils import get_attrs, update_attrs
from core.views import CoreDeleteView

from mozdns.domain.models import Domain
from mozdns.address_record.models import AddressRecord
from mozdns.ptr.models import PTR

import pdb
import ipaddr


def delete_static_interface(reqeust, intr_pk):
    intr = get_object_or_404(StaticInterface, pk=intr_pk)
    system = intr.system
    try:
        intr.delete()
    except ValidationError, e:
        pass
    return redirect(system)

def delete_attr(request, system_pk, intr_pk, attr_pk):
    """
    An view destined to be called by ajax to remove an attr.
    """
    #system = get_object_or_404(System, pk=system_pk)
    #intr = get_object_or_404(StaticInterface, pk=intr_pk)
    attr = get_object_or_404(StaticIntrKeyValue, pk=attr_pk)
    attr.delete()
    return HttpResponse("Attribute Removed.")


def edit_static_interface(request, intr_pk):
    # TODO, make sure the user has access to this system
    intr = get_object_or_404(StaticInterface, pk=intr_pk)
    system = intr.system
    attrs = intr.staticintrkeyvalue_set.all()
    if request.method == 'POST':
        interface_form = StaticInterfaceForm(request.POST, instance=intr)
        if interface_form.is_valid():
            try:
                # Handle key value stuff.
                kv = get_attrs(request.POST)
                update_attrs(kv, attrs, StaticIntrKeyValue, intr, 'intr')
                intr = interface_form.save()

                # Everything checks out. Clean and Save all the objects.
                intr.clean()
                intr.save()
            except ValidationError, e:
                interface_form._errors['__all__'] = ErrorList(e.messages)
                return render(request, 'static_intr/static_intr_edit.html', {
                    'form': interface_form,
                    'intr': intr,
                    'intr_attrs': attrs,
                    'form_title': 'Edit Interface for System {0}'.format(
                        system),
                    'domain': intr.domain
                })
        else:
            raise ValidationError(interface_form.errors)

        messages.success(request, "Success! Interface Updated.")
        return redirect(system)

    else:
        interface_form = StaticInterfaceForm(instance=intr)
        return render(request, 'static_intr/static_intr_edit.html', {
            'form': interface_form,
            'intr': intr,
            'intr_attrs': attrs,
            'form_title': 'Edit Interface for System {0}'.format(system),
            'domain': intr.domain
        })

def create_static_interface(request, system_pk):
    # TODO, make sure the user has access to this system
    system = get_object_or_404(System, pk=system_pk)
    if request.method == 'POST':
        interface_form = StaticInterfaceForm(request.POST)

        a, ptr, r = None, None, None
        if interface_form.is_valid():
            try:
                ip_str = interface_form.cleaned_data['ip']
                label = interface_form.cleaned_data['label']
                domain = interface_form.cleaned_data['domain']
                ip_type = interface_form.cleaned_data['ip_type']

                intr = StaticInterface(label=label, domain=domain,
                        ip_str=ip_str,
                    ip_type=ip_type, system=system)
                intr.clean()
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

def find_available_ip_from_ipv4_network(net):
    net.update_network()

    start = int(net.network.network)
    end = int(net.network.broadcast)
    if start >= end -1:
        return HttpResponse("Too small of network.")

    records = AddressRecord.objects.filter(ip_upper = 0, ip_lower__gte = start,
            ip_lower__lte = end)
    intrs = StaticInterface.objects.filter(ip_upper = 0, ip_lower__gte = start,
            ip_lower__lte = end)
    if not records and not intrs:
        ip = ipaddr.IPv4Address(start + 10)
        return ip
    for i in range(start + 10, end-1):
        taken = False
        for record in records:
            if record.ip_lower == i:
                taken = True
                break
        if taken == False:
            for intr in intrs:
                if intr.ip_lower == i:
                    taken = True
                    break
        if taken == False:
            ip = ipaddr.IPv4Address(i)
            return ip
    return None

def quick_create(request, system_pk):
    # TODO, make sure the user has access to this system
    system = get_object_or_404(System, pk=system_pk)
    if request.method == 'POST':
        interface_form = StaticInterfaceQuickForm(request.POST)

        a, ptr, r = None, None, None
        if interface_form.is_valid():
            try:
                #mac = interface_form.cleaned_data['mac']
                label = interface_form.cleaned_data['label']
                ip_type = interface_form.cleaned_data['ip_type']
                vlan = interface_form.cleaned_data['vlan']
                site = interface_form.cleaned_data['site']

                networks = []
                for network in vlan.network_set.all():
                    if network.site.get_site_path() == site.get_site_path():
                        networks.append(network)
                if not networks:
                    raise ValidationError("No appropriate networks found. "
                        "Consider adding this interface manually.")

                for network in networks:
                    ip = find_available_ip_from_ipv4_network(network)
                    if ip:
                        break
                if ip == None:
                    raise ValidationError("No appropriate IP found "
                        "in {0} Vlan {1}. Consider adding this interface "
                        "manually.".format(site.name, vlan.name))

                expected_name = "{0}.{1}.mozilla.com".format(vlan.name,
                    site.get_site_path())
                print "Expected name {0}".format(expected_name)
                try:
                    domain = Domain.objects.get(name=expected_name)
                except ObjectDoesNotExist, e:
                    raise ValidationError("The domain {0} doesn't seem to "
                        "exist. Consider creating this interface manually.")

                intr = StaticInterface(label=label, domain=domain,
                        ip_str=str(ip),
                    #ip_type=ip_type, mac=mac, system=system)
                    ip_type=ip_type, system=system)
                intr.full_clean()
                intr.save()
            except ValidationError, e:
                interface_form._errors['__all__'] = ErrorList(e.messages)
                return render(request, 'static_intr/static_intr_form.html', {
                    'form': interface_form,
                    'form_title': 'Quick Interface Create for System {0}'.format(
                        system)
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
