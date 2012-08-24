from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect

from mozdns.address_record.models import AddressRecord
from mozdns.ptr.models import PTR
from mozdns.domain.models import Domain

import simplejson as json
import pdb

def mozdns_home(request):
    domains = Domain.objects.filter(is_reverse=False).order_by('name').order_by('soa__comment')
    return render(request, 'mozdns/mozdns.html', {
        'domains': domains,
    })

def commit_record(request):
    pdb.set_trace()
    commit_data = json.loads(request.raw_post_data)
    record_type = commit_data.pop("rtype", None)
    if not record_type:
        commit_data["errors"] = {"__all__":"No record type."}
        return HttpResponse(return_data)
    if record_type == "A":
        commit_data = add_ip_type_to_commit(commit_data)
        commit_data = add_domain_to_commit(commit_data)
        Klass = AddressRecord
    elif record_type == "PTR":
        commit_data = add_ip_type_to_commit(commit_data)
        Klass = PTR

    try:
        obj = Klass(**commit_data)
    except ValueError, e:
        commit_data["errors"] = e.message_dict
        return return_without_domain(commit_data)

    try:
        obj.full_clean()
    except ValidationError, e:
        commit_data["errors"] = e.message_dict
        print commit_data
        return return_without_domain(commit_data)
    try:
        obj.save()
    except ValidationError, e:
        commit_data["errors"] = e.message_dict
        return return_without_domain(commit_data)

    commit_data['success'] = obj.get_absolute_url()
    return return_without_domain(commit_data)


def return_without_domain(commit_data):
    if "domain" in commit_data:
        commit_data["domain"] = commit_data["domain"].name
    return_data = json.dumps(commit_data)
    return HttpResponse(return_data)


def add_ip_type_to_commit(commit_data):
    # Let's guess the IP type. ':' means IPv6
    ip_str = commit_data.get("ip_str", "")
    if ip_str.find(':') > -1:
        commit_data["ip_type"] = '6'
    else:
        commit_data["ip_type"] = '4'
    return commit_data


def add_domain_to_commit(commit_data):
    commit_data["domain"] = get_object_or_404(Domain,
            name=commit_data["domain"])
    return commit_data
