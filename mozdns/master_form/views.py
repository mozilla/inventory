from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Q
from django.http import QueryDict
from django.forms.util import ErrorList, ErrorDict
from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404

from mozdns.address_record.models import AddressRecord
from mozdns.address_record.forms import AddressRecordFQDNForm
from mozdns.address_record.forms import AddressRecordForm
from mozdns.ptr.models import PTR
from mozdns.ptr.forms import PTRForm
from mozdns.srv.models import SRV
from mozdns.srv.forms import SRVForm, FQDNSRVForm
from mozdns.txt.models import TXT
from mozdns.txt.forms import TXTForm, FQDNTXTForm
from mozdns.mx.models import MX
from mozdns.mx.forms import MXForm, FQDNMXForm
from mozdns.cname.models import CNAME
from mozdns.cname.forms import CNAMEFQDNForm, CNAMEForm
from mozdns.domain.models import Domain
from mozdns.view.models import View
from mozdns.utils import ensure_label_domain
from mozdns.utils import prune_tree
import operator

from gettext import gettext as _, ngettext
import simplejson as json
import pdb


def get_klasses(record_type):
    if record_type == "A":
        Klass = AddressRecord
        FormKlass = AddressRecordForm
        FQDNFormKlass = AddressRecordFQDNForm
    elif record_type == "PTR":
        Klass = PTR
        FormKlass = PTRForm
        FQDNFormKlass = PTRForm
    elif record_type == "SRV":
        Klass = SRV
        FormKlass = SRVForm
        FQDNFormKlass = FQDNSRVForm
    elif record_type == "CNAME":
        Klass = CNAME
        FormKlass = CNAMEForm
        FQDNFormKlass = CNAMEFQDNForm
    elif record_type == "TXT":
        Klass = TXT
        FormKlass = TXTForm
        FQDNFormKlass = FQDNTXTForm
    elif record_type == "MX":
        Klass = MX
        FormKlass = MXForm
        FQDNFormKlass = FQDNMXForm
    else:
        Klass, FormKlass, FQDNFormKlass = None, None, None

    return Klass, FormKlass, FQDNFormKlass

def mozdns_record_search_ajax(request):
    """This function will return a list of records matching the 'query' of type
    'record_type'. It's used for ajaxy stuff."""
    query = request.GET.get('term', '')
    record_type = request.GET.get('record_type', '')
    if not query or not record_type:
        raise Http404
    Klass, _, _ = get_klasses(record_type)
    mega_filter = [Q(**{"{0}__icontains".format(field): query}) for field in
            Klass.search_fields]
    mega_filter = reduce(operator.or_, mega_filter)
    records = Klass.objects.filter(mega_filter)[:15]
    records = [{'label': str(record), 'pk': record.pk} for record in records]
    return HttpResponse(json.dumps(records))


def mozdns_record_form_ajax(request):
    record_type = request.GET.get('record_type')
    record_pk = request.GET.get('record_pk', '')
    Klass, FormKlass, FQDNFormKlass = get_klasses(record_type)

    if not record_type:
        raise Http404
    if record_pk:
        try:
            object_ = Klass.objects.get(pk=record_pk)
            # ACLs should be appplied here
            form = FQDNFormKlass(instance=object_)
        except ObjectDoesNotExist:
            form = FQDNFormKlass()
            record_pk = ''
    else:
        form = FQDNFormKlass()

    if record_pk:
        message = _("Change some data and press 'Commit' to update the "
                    "{0}".format(record_type))
    else:
        message = _("Enter some data and press 'Commit' to create a new "
                    "{0}".format(record_type))
    return render(request, 'master_form/ajax_form.html', {
        'record_type': record_type,
        'record_pk': record_pk,
        'form': form,
        'message': message
    })

def mozdns_record(request):
    if request.method == 'GET':
        record_type = str(request.GET.get('record_type', 'A'))
        record_pk = str(request.GET.get('record_pk', ''))
        domains = Domain.objects.filter(is_reverse=False)
        return render(request, 'master_form/master_form.html', {
            'record_type': record_type,
            'record_pk': record_pk,
            'domains': json.dumps([domain.name for domain in domains]),
        })

    if request.method != 'POST':
        raise Http404

    qd = request.POST.copy()  # make qd mutable
    orig_qd = request.POST.copy()  # If there are ever errors, we use this qd
        # to populate the form we send to the user
    record_type = qd.pop('record_type', '')
    if record_type:
        record_type = record_type[0]
    record_pk = qd.pop('record_pk', '')
    if record_pk:
        record_pk = record_pk[0]
    if not record_type:
        raise Http404
    Klass, FormKlass, FQDNFormKlass = get_klasses(record_type)
    if 'fqdn' in qd:
        fqdn = qd.pop('fqdn')
        fqdn = fqdn[0]
    domain = None
    if record_type == 'PTR':
        pass
    else:
        try:
            label, domain = ensure_label_domain(fqdn)
            # If something goes bad latter on you must call prune_tree on
            # domain.  If you don't do this there will be a domain leak.
        except ValidationError, e:
            form = FQDNFormKlass(orig_qd)
            form._errors = ErrorDict()
            form._errors['__all__'] = ErrorList(e.messages)
            return render(request, 'master_form/ajax_form.html', {
                'form': form,
                'record_type': record_type,
                'record_pk': record_pk,
            })
        qd['label'], qd['domain'] = label, str(domain.pk)

    if record_pk:
        object_ = get_object_or_404(Klass, pk=record_pk)
        # ACLs should be appplied here. Maybe move this up a bit so we don't
        # create new domains for unauthorized users.
        form = FormKlass(qd, instance=object_)
    else:
        form = FormKlass(qd)

    if form.is_valid():
        try:
            object_ = form.save()
        except ValidationError, e:
            prune_tree(domain)
            error_form = FQDNFormKlass(orig_qd)
            error_form._errors = ErrorDict()
            error_form._errors['__all__'] = ErrorList(e.messages)
            return render(request, 'master_form/ajax_form.html', {
                'form': error_form,
                'record_type': record_type,
                'record_pk': record_pk,
            })

        fqdn_form = FQDNFormKlass(instance=object_)
        if record_pk:
            message = 'Record Updated!'
        else:
            message = 'Record Created!'
        return render(request, 'master_form/ajax_form.html', {
            'form': fqdn_form,
            'record_type': record_type,
            'record_pk': object_.pk,
            'message': message
        })
    else:
        prune_tree(domain)
        error_form = FQDNFormKlass(orig_qd)
        error_form._errors = form._errors
        return render(request, 'master_form/ajax_form.html', {
            'form': error_form,
            'record_type': record_type,
            'record_pk': record_pk,
        })
