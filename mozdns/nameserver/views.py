from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404, redirect, render
from django.forms.util import ErrorList, ErrorDict


from mozdns.nameserver.forms import NameserverForm
from mozdns.nameserver.forms import NSDelegated
from mozdns.nameserver.models import Nameserver
from mozdns.views import (MozdnsDeleteView, MozdnsDetailView, MozdnsListView,
                          MozdnsCreateView, MozdnsUpdateView)

from mozdns.address_record.models import AddressRecord
from mozdns.domain.models import Domain
from core.interface.static_intr.models import StaticInterface


class NSView(object):
    model = Nameserver
    form_class = NameserverForm
    queryset = Nameserver.objects.all()


class NSDeleteView(NSView, MozdnsDeleteView):
    """ """


class NSDetailView(NSView, MozdnsDetailView):
    template_name = "nameserver/nameserver_detail.html"


class NSListView(NSView, MozdnsListView):
    """ """
    template_name = "nameserver/nameserver_list.html"
    queryset = Nameserver.objects.all().select_related()
    # Wooo. Huge speed boost because of select_related


class NSCreateView(NSView, MozdnsCreateView):
    """ """


def update_ns(request, nameserver_pk):
    nameserver = get_object_or_404(Nameserver, pk=nameserver_pk)
    if request.method == "POST":
        form = NameserverForm(request.POST, instance=nameserver)
        try:
            if form.is_valid():
                server = form.cleaned_data['server']
                domain = form.cleaned_data['domain']
                if 'glue' in form.cleaned_data:
                    glue_type, glue_pk = form.cleaned_data['glue'].split('_')
                    try:
                        if glue_type == 'addr':
                            glue = AddressRecord.objects.get(pk=glue_pk)
                        elif glue_type == 'intr':
                            glue = StaticInterface.objects.get(pk=glue_pk)
                    except ObjectDoesNotExist, e:
                        raise ValidationError("Couldn't find glue: " + str(e))
                    nameserver.glue = glue
                nameserver.server = server
                nameserver.domain = domain
                nameserver.clean()
                nameserver.save()
        except ValidationError, e:
            form = Nameserver(instance=nameserver)
            if form._errors is None:
                form._errors = ErrorDict()
            form._errors['__all__'] = ErrorList(e.messages)

        return redirect(nameserver)
    else:
        form = NameserverForm(instance=nameserver)
    return render(request, "mozdns/mozdns_form.html", {
        'form': form
    })


class NSUpdateView(NSView, MozdnsUpdateView):
    """ """


def create_ns_delegated(request, domain):
    if request.method == "POST":
        form = NSDelegated(request.POST)
        domain = Domain.objects.get(pk=domain)
        if not domain:
            pass  # Fall through. Maybe send a message saying no domain?
        elif form.is_valid():
            was_delegated = domain.delegated
            if was_delegated:
                # Quickly and transperently Un-delegate the domain so we
                # can add an address record.
                domain.delegated = False
                domain.save()
            if was_delegated:
                # Reset delegation status
                domain.delegated = True
                domain.save()

        else:
            pass  # Fall through
    # Everything else get's the blank form
    form = NSDelegated()
    return render_to_response("nameserver/ns_delegated.html",
                              {'form': form, 'request': request})
