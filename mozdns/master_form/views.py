from django.core.exceptions import ObjectDoesNotExist, ValidationError
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
from mozdns.srv.models import SRV
from mozdns.txt.models import TXT
from mozdns.mx.models import MX
from mozdns.cname.models import CNAME
from mozdns.cname.forms import CNAMEFQDNForm, CNAMEForm
from mozdns.domain.models import Domain
from mozdns.nameserver.models import Nameserver
from mozdns.view.models import View
from mozdns.utils import ensure_label_domain
from mozdns.utils import prune_tree

import simplejson as json
import pdb


def get_klasses(record_type):
    if record_type == "A":
        Klass = AddressRecord
        FormKlass = AddressRecordForm
        FQDNFormKlass = AddressRecordFQDNForm
    elif record_type == "PTR":
        commit_data = add_ip_type_to_commit(commit_data)
        Klass = PTR
    elif record_type == "SRV":
        commit_data = add_domain_to_commit(commit_data)
        Klass = SRV
    elif record_type == "CNAME":
        Klass = CNAME
        FormKlass = CNAMEForm
        FQDNFormKlass = CNAMEFQDNForm
    elif record_type == "NS":
        commit_data = add_domain_to_commit(commit_data)
        Klass = Nameserver
    elif record_type == "TXT":
        commit_data = add_domain_to_commit(commit_data)
        Klass = TXT
    elif record_type == "MX":
        commit_data = add_domain_to_commit(commit_data)
        Klass = MX
    return Klass, FormKlass, FQDNFormKlass

def mozdns_record_form_ajax(request):
    record_type = request.GET.get('record_type')
    record_pk = request.GET.get('record_pk', '')
    _, FormKlass, FQDNFormKlass = get_klasses(record_type)
    return render(request, 'master_form/ajax_form.html', {
        'record_type': record_type,
        'record_pk': record_pk,
        'form': FQDNFormKlass()
    })

def mozdns_record(request):
    if request.method == 'GET':
        record_type = request.GET.get('record_type', '')
        record_pk = request.GET.get('record_pk', '')
        domains = Domain.objects.filter(is_reverse=False)
        return render(request, 'master_form/master_form.html', {
            'record_type': record_type,
            'record_pk': record_pk,
            'domains': json.dumps([domain.name for domain in domains]),
            'address_record_form': AddressRecordFQDNForm(),
            'cname_record_form': CNAMEFQDNForm()
        })
    if request.method != 'POST':
        raise Http404

    record_type = request.POST.get('record_type', '')
    record_pk = request.POST.get('record_pk', '')
    if not record_type:
        raise Http404
    Klass, FormKlass, FQDNFormKlass = get_klasses(record_type)
    form_data = {}
    for key, value in request.POST.iteritems():
        form_data[key] = value
    try:
        if form_data['fqdn'] != '':
            label_domain = ensure_label_domain(form_data['fqdn'])
        else:
            label_domain = '', ''  # Let's cause errors
        form_data.pop('fqdn')
    except ValidationError, e:
        form = FormKlass()
        form._errors = ErrorDict()
        form._errors['__all__'] = ErrorList(e.messages)
        return render(request, 'master_form/ajax_form.html', {
            'form': form,
            'record_type': record_type,
            'record_pk': record_pk,
        })
    form_data.pop('record_type')
    form_data.pop('record_pk')

    if record_pk:
        object_ = get_object_or_404(Klass, pk=record_pk)
        form = FormKlass(form_data, instance=object_)
    else:
        qd = QueryDict({}, mutable=True)
        qd.update(form_data)
        form = FormKlass(qd)


    if form.is_valid():
        object_ = form.save()
        return HttpResponse('Success object pk is '+ object_)
    else:
        error_form = FQDNFormKlass()
        error_form._errors = form._errors
        return render(request, 'master_form/ajax_form.html', {
            'form': error_form,
        })
