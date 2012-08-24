from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404

from mozdns.address_record.models import AddressRecord
from mozdns.ptr.models import PTR
from mozdns.srv.models import SRV
from mozdns.txt.models import TXT
from mozdns.mx.models import MX
from mozdns.cname.models import CNAME
from mozdns.domain.models import Domain
from mozdns.nameserver.models import Nameserver
from mozdns.view.models import View

import simplejson as json
import pdb

def mozdns_home(request):
    domains = Domain.objects.filter(is_reverse=False).order_by(
                'name').order_by('soa__comment')
    return render(request, 'mozdns/mozdns.html', {
        'domains': domains,
    })

def commit_record(request):
    commit_data = json.loads(request.raw_post_data)
    record_type = commit_data.pop("rtype", None)
    if not record_type:
        raise Http404
    if record_type == "A":
        commit_data = add_ip_type_to_commit(commit_data)
        commit_data = add_domain_to_commit(commit_data)
        Klass = AddressRecord
    elif record_type == "PTR":
        commit_data = add_ip_type_to_commit(commit_data)
        Klass = PTR
    elif record_type == "SRV":
        commit_data = add_domain_to_commit(commit_data)
        Klass = SRV
    elif record_type == "CNAME":
        commit_data = add_domain_to_commit(commit_data)
        Klass = CNAME
    elif record_type == "NS":
        commit_data = add_domain_to_commit(commit_data)
        Klass = Nameserver
    elif record_type == "TXT":
        commit_data = add_domain_to_commit(commit_data)
        Klass = TXT
    elif record_type == "MX":
        commit_data = add_domain_to_commit(commit_data)
        Klass = MX
    views = extract_views(commit_data)
    existing_obj = get_object_to_update(commit_data, Klass)
    if not existing_obj:
        try:
            obj = Klass(**commit_data)
        except ValueError, e:
            commit_data["errors"] = e.message_dict
            return return_without_domain(commit_data)
        created = True
    else:
        created = False
        obj = apply_commit(existing_obj, commit_data)

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

    orig_views = [view for view in obj.views.all()]
    for view in orig_views:
        obj.views.remove(view)
    # First kill all the views because are just going to replace them.
    for view in views:
        obj.views.add(view)

    commit_data['success'] = obj.get_absolute_url()
    commit_data['obj_pk'] = obj.pk
    commit_data['obj_class'] = obj.__class__.__name__
    if created:
        commit_data['created'] = True
    else:
        commit_data['created'] = False
    return return_without_domain(commit_data)


def return_without_domain(commit_data):
    if "domain" in commit_data:
        commit_data["domain"] = commit_data["domain"].name
    return_data = json.dumps(commit_data)
    return HttpResponse(return_data)


def extract_views(commit_data):
    """This function nukes the views from commit_data"""
    views = []
    is_public = commit_data.pop("public_view", False)
    if is_public:
        public, _ = View.objects.get_or_create(name="public")
        views.append(public)
    is_private = commit_data.pop("private_view", False)
    if is_private:
        private, _ = View.objects.get_or_create(name="private")
        views.append(private)
    return views


def get_object_to_update(commit_data, Klass):
    pk = commit_data.pop("pk", None)
    if not pk:
        return None
    obj = Klass.objects.get(pk=pk)
    return obj

def apply_commit(obj, commit_data):
    # this is a test... never do this at home
    for k, v in commit_data.iteritems():
        setattr(obj, k, v)
    return obj


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
