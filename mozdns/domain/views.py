import simplejson as json

from django.contrib import messages
from django.forms import ValidationError
from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic import UpdateView
from django.views.generic import DetailView
from django.views.generic import CreateView

from mozdns.utils import tablefy
from mozdns.views import MozdnsDeleteView, MozdnsListView
from mozdns.domain.models import Domain
from mozdns.domain.forms import DomainForm, DomainUpdateForm


def domain_sort(domains):
    """
    This is soooooo slow.
    """

    roots = domains.filter(master_domain=None)
    ordered = []
    for root in roots:
        ordered += build_tree(root, domains)
    return ordered


def build_tree(root, domains):
    if len(domains) == 0:
        return root
    ordered = [root]
    children = domains.filter(master_domain=root)
    for child in children:
        ordered += build_tree(child, domains)
    return ordered


def get_all_domains(request):
    domains = [domain.name for domain in Domain.objects.all()]
    return HttpResponse(json.dumps(domains))


class DomainView(object):
    model = Domain
    queryset = Domain.objects.all().order_by('name')
    form_class = DomainForm


class DomainDeleteView(DomainView, MozdnsDeleteView):
    """ """


class DomainListView(DomainView, MozdnsListView):
    queryset = Domain.objects.filter(is_reverse=False)
    template_name = "domain/domain_list.html"


class ReverseDomainListView(DomainView, MozdnsListView):
    queryset = Domain.objects.filter(is_reverse=True).order_by('name')


class DomainDetailView(DomainView, DetailView):
    template_name = "domain/domain_detail.html"

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        domain = kwargs.get('object', False)
        if not domain:
            return context

        # TODO this process can be generalized. It's not very high priority.
        mx_objects = domain.mx_set.all().order_by('label')
        mx_headers, mx_matrix, mx_urls = tablefy(mx_objects)

        srv_objects = domain.srv_set.all().order_by('label')
        srv_headers, srv_matrix, srv_urls = tablefy(srv_objects)

        txt_objects = domain.txt_set.all().order_by('label')
        txt_headers, txt_matrix, txt_urls = tablefy(txt_objects)

        sshfp_objects = domain.sshfp_set.all().order_by('label')
        sshfp_headers, sshfp_matrix, sshfp_urls = tablefy(sshfp_objects)

        cname_objects = domain.cname_set.order_by('label')
        if cname_objects.count() > 50:
            cname_views = False
        else:
            cname_views = True
        cname_headers, cname_matrix, cname_urls = tablefy(cname_objects,
                                                          cname_views)

        # TODO, include Static Registrations
        ptr_objects = domain.ptr_set.all().order_by('ip_str')
        ptr_headers, ptr_matrix, ptr_urls = tablefy(ptr_objects)

        # TODO, include Static Registrations
        intr_objects = domain.staticinterface_set.all().order_by(
            'name').order_by('ip_str')
        intr_headers, intr_matrix, intr_urls = tablefy(intr_objects)

        address_objects = domain.addressrecord_set.all().order_by('label')
        # This takes too long to load more than 50.
        if address_objects.count() > 50:
            adr_views = False
        else:
            adr_views = True
        adr_headers, adr_matrix, adr_urls = tablefy(address_objects, adr_views)

        ns_objects = domain.nameserver_set.all().order_by('server')
        ns_headers, ns_matrix, ns_urls = tablefy(ns_objects)

        # Join the two dicts
        context = dict({
            "ns_headers": ns_headers,
            "ns_matrix": ns_matrix,
            "ns_urls": ns_urls,

            "address_headers": adr_headers,
            "address_matrix": adr_matrix,
            "address_urls": adr_urls,
            "address_views": adr_views,

            "mx_headers": mx_headers,
            "mx_matrix": mx_matrix,
            "mx_urls": mx_urls,

            "srv_headers": srv_headers,
            "srv_matrix": srv_matrix,
            "srv_urls": srv_urls,

            "txt_headers": txt_headers,
            "txt_matrix": txt_matrix,
            "txt_urls": txt_urls,

            "sshfp_headers": sshfp_headers,
            "sshfp_matrix": sshfp_matrix,
            "sshfp_urls": sshfp_urls,

            "cname_headers": cname_headers,
            "cname_matrix": cname_matrix,
            "cname_urls": cname_urls,
            "cname_views": cname_views,

            "ptr_headers": ptr_headers,
            "ptr_matrix": ptr_matrix,
            "ptr_urls": ptr_urls,

            "intr_headers": intr_headers,
            "intr_matrix": intr_matrix,
            "intr_urls": intr_urls
        }.items() + context.items())

        return context


class DomainCreateView(DomainView, CreateView):
    model_form = DomainForm

    def post(self, request, *args, **kwargs):
        domain_form = DomainForm(request.POST)
        # Try to create the domain. Catch all exceptions.
        try:
            domain = domain_form.save()
        except ValueError:
            return render(request, "mozdns/mozdns_form.html", {
                'form': domain_form,
                'form_title': 'Create Domain'
            })

        try:
            if domain.master_domain and domain.master_domain.soa:
                domain.soa = domain.master_domain.soa
                domain.save()
        except ValidationError:
            return render(request, "mozdns/mozdns_form.html", {'form':
                          domain_form, 'form_title': 'Create Domain'})
        # Success. Redirect.
        messages.success(request, "{0} was successfully created.".
                         format(domain.name))
        return redirect(domain)

    def get(self, request, *args, **kwargs):
        domain_form = DomainForm()
        return render(request, "mozdns/mozdns_form.html",
                      {'form': domain_form, 'form_title': 'Create Domain'})


class DomainUpdateView(DomainView, UpdateView):
    form_class = DomainUpdateForm
    template_name = "mozdns/mozdns_update.html"
