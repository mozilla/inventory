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
from core.keyvalue.utils import get_attrs, update_attrs

from mozdns.domain.models import Domain
from mozdns.address_record.models import AddressRecord
from mozdns.ptr.models import PTR

import re
import pdb
import ipaddr


is_attr = re.compile("^attr_\d+$")


def delete_attr(request, system_pk, intr_pk, attr_pk):
    """
    An view destined to be called by ajax to remove an attr.
    """
    #system = get_object_or_404(System, pk=system_pk)
    #intr = get_object_or_404(StaticInterface, pk=intr_pk)
    attr = get_object_or_404(StaticIntrKeyValue, pk=attr_pk)
    attr.delete()
    return HttpResponse("Attribute Removed.")


def edit_static_interface(request, system_pk, intr_pk):
    # TODO, make sure the user has access to this system
    system = get_object_or_404(System, pk=system_pk)
    intr = get_object_or_404(StaticInterface, pk=intr_pk)
    attrs = intr.staticintrkeyvalue_set.all()
    if request.method == 'POST':
        interface_form = StaticInterfaceForm(request.POST)
        if interface_form.is_valid():
            try:
                intr.ip_str = interface_form.cleaned_data['ip']
                #intr.mac = interface_form.cleaned_data['mac']
                intr.label = interface_form.cleaned_data['hostname']
                intr.domain = interface_form.cleaned_data['domain']
                intr.ip_type = interface_form.cleaned_data['ip_type']

                # Handle key value stuff.
                kv = get_attrs(request.POST)
                update_attrs(kv, attrs, StaticIntrKeyValue, intr, 'intr')

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

        messages.success(request, "Success! Interface Updated.")
        return redirect(system)

    else:
        initial_vals = {'ip':intr.ip_str, 'ip_type':intr.ip_type,
                #'mac':intr.mac, 'hostname':intr.label,
                'hostname':intr.label,
                'domain': intr.domain}
        interface_form = StaticInterfaceForm(initial=initial_vals)
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
                #mac = interface_form.cleaned_data['mac']
                hostname = interface_form.cleaned_data['hostname']
                domain = interface_form.cleaned_data['domain']
                ip_type = interface_form.cleaned_data['ip_type']

                intr = StaticInterface(label=hostname, domain=domain,
                        ip_str=ip_str,
                    #ip_type=ip_type, mac=mac, system=system)
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

def find_available_ip_from_network(request):
    print "-" * 20
    try:
        ip = ipaddr.IPv4Network(request.GET['network'])
    except ipaddr.AddressValueError, e:
        return HttpResponse("Invalid Network.")

    start = int(ip.network)
    end = int(ip.broadcast)
    if start >= end -1:
        return HttpResponse("Too small of network.")

    records = AddressRecord.objects.filter(ip_upper = 0, ip_lower__gte = start,
            ip_lower__lte = end)
    if not records:
        ip = ipaddr.IPv4Address(start + 10)
        return HttpResponse(str(ip))
    for i in range(start + 10, end-1):
        taken = False
        for record in records:
            if record.ip_lower == i:
                taken = True
                break
        if taken == False:
            ip = ipaddr.IPv4Address(i)
            return HttpResponse(str(ip))
    return HttpResponse("None")
