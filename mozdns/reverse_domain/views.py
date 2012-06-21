from django import forms
from django.contrib import messages
from django.forms import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render, render_to_response
from django.views.generic import DetailView, ListView, CreateView, UpdateView

from mozdns.nameserver.reverse_nameserver.models import ReverseNameserver
from mozdns.reverse_domain.models import boot_strap_ipv6_reverse_domain
from mozdns.reverse_domain.models import ReverseDomain
from mozdns.reverse_domain.forms import BootStrapForm
from mozdns.reverse_domain.forms import ReverseDomainForm
from mozdns.reverse_domain.forms import ReverseDomainUpdateForm
from mozdns.soa.models import SOA
from mozdns.utils import tablefy
from mozdns.views import MozdnsDeleteView


class ReverseDomainView(object):
    queryset = ReverseDomain.objects.all()
    form_class = ReverseDomainForm


class ReverseDomainDeleteView(ReverseDomainView, MozdnsDeleteView):
    """ """


class ReverseDomainListView(ReverseDomainView, ListView):
    """
    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        ip4_rdoms = ReverseDomain.objects.filter(ip_type='4')
        ip6_rdoms = ReverseDomain.objects.filter(ip_type='6')

        rdom4_headers, rdom4_matrix, rdom4_urls = tablefy(ip4_rdoms)
        rdom6_headers, rdom6_matrix, rdom6_urls = tablefy(ip6_rdoms)

        context = dict({
            "rdom4_headers": rdom4_headers,
            "rdom4_matrix": rdom4_matrix,
            "rdom4_urls": rdom4_urls,

            "rdom6_headers": rdom6_headers,
            "rdom6_matrix": rdom6_matrix,
            "rdom6_urls": rdom6_urls,
        }.items() + context.items())

        return context
    """


class ReverseDomainDetailView(ReverseDomainView, DetailView):

    def get_context_data(self, **kwargs):
        context = super(ReverseDomainDetailView, self).get_context_data(
                                                                **kwargs)

        reverse_domain = kwargs.get('object', False)
        if not reverse_domain:
            return context

        # TODO this process can be generalized. It's not very high priority.
        revns_objects = ReverseNameserver.objects.filter(
                                        reverse_domain=reverse_domain)

        revns_headers, revns_matrix, revns_urls = tablefy(revns_objects)

        # Join the two dicts
        context = dict({
            "revns_headers": revns_headers,
            "revns_matrix": revns_matrix,
            "revns_urls": revns_urls,
        }.items() + context.items())

        return context


class ReverseDomainCreateView(ReverseDomainView, CreateView):
    form_class = ReverseDomainForm
    template_name = 'mozdns/mozdns_form.html'

    def post(self, request, *args, **kwargs):
        reverse_domain_form = ReverseDomainForm(request.POST)

        # Try to create the reverse_domain. Catch all exceptions.
        try:
            reverse_domain = reverse_domain_form.save(commit=False)
        except ValueError, e:
            return render(request, "mozdns/mozdns_form.html", {
                'form': reverse_domain_form,
                'form_title': 'Create Reverse Domain'
            })

        if (reverse_domain_form.cleaned_data['inherit_soa'] and
            reverse_domain.master_reverse_domain):
            reverse_domain.soa = reverse_domain.master_reverse_domain.soa

        try:
            reverse_domain.save()
        except ValidationError, e:
            return render(request, "mozdns/mozdns_form.html", {
                'form': reverse_domain_form,
                'form_title': 'Create Reverse Domain'
            })

        # Success. Redirect.
        messages.success(request, '{0} was successfully created.'.
                         format(reverse_domain.name))

        return redirect(reverse_domain)

    def get(self, request, *args, **kwargs):
        reverse_domain_form = ReverseDomainForm()
        return render(request, "mozdns/mozdns_form.html", {
            'form': reverse_domain_form,
            'form_title': 'Create Reverse Domain'
        })

class ReverseDomainUpdateView(ReverseDomainView, UpdateView):
    form_class = ReverseDomainUpdateForm
    template_name = 'mozdns/mozdns_update.html'

    def post(self, request, *args, **kwargs):
        reverse_domain = get_object_or_404(ReverseDomain,
                                           pk=kwargs.get('pk', 0))
        try:
            reverse_domain_form = ReverseDomainUpdateForm(request.POST)
            new_soa_pk = reverse_domain_form.data.get('soa', None)
            if new_soa_pk:
                new_soa = SOA.objects.get(pk=new_soa_pk)
                reverse_domain.soa = new_soa

            if reverse_domain.soa and not new_soa_pk:
                reverse_domain.soa = None

            if (reverse_domain_form.data.get('inherit_soa', False) and
                reverse_domain.master_reverse_domain):
                reverse_domain.soa = reverse_domain.master_reverse_domain.soa
            reverse_domain.save()  # Major exception handling logic
                                   # happens here.
        except ValueError, e:
            rev_domain_form = ReverseDomainUpdateForm(instance=reverse_domain)
            messages.error(request, str(e))
            return render(request, "mozdns/mozdns_update.html", {
                            "reverse_domain_form": rev_domain_form,
                        })

        messages.success(request, '{0} was successfully updated.'.
                         format(reverse_domain.name))
        return redirect(reverse_domain)

    def get(self, request, *args, **kwargs):
        ret = super(ReverseDomainUpdateView, self).get(request, *args, **kwargs)
        return ret


def bootstrap_ipv6(request):

    if request.method == 'POST':
        bootstrap_form = BootStrapForm(request.POST)

        if bootstrap_form.is_valid():
            if bootstrap_form.data['soa'] == '':
                soa = None
            else:
                soa = get_object_or_404(SOA, pk=bootstrap_form.data['soa'])

            try:
                reverse_domain = boot_strap_ipv6_reverse_domain(
                    bootstrap_form.cleaned_data['name'],
                    soa=soa
                )
            except ValidationError, e:
                messages.error(request, str(e))
                return render(request, 'mozdns/mozdns_form.html', {
                    'form': bootstrap_form,
                    'form_title': 'Bootstrap IPv6 Reverse Domain'
                })

        else:
            return render(request, 'mozdns/mozdns_form.html', {
                'form': bootstrap_form,
                'form_title': 'Bootstrap IPv6 Reverse Domain'
            })

        messages.success(request, "Success! Bootstrap complete. You are "
            "now looking at the leaf reverse domain."
        )
        return redirect(reverse_domain)

    else:
        bootstrap_form = BootStrapForm()
        return render(request, 'mozdns/mozdns_form.html', {
            'form': bootstrap_form,
            'form_title': 'Bootstrap IPv6 Reverse Domain'
        })


def inheirit_soa(request, pk):
    reverse_domain = get_object_or_404(ReverseDomain, pk=pk)

    if request.method == 'POST':
        if reverse_domain.master_reverse_domain:
            reverse_domain.soa = reverse_domain.master_reverse_domain.soa
            reverse_domain.save()
            messages.success(request, '{0} was successfully updated.'.
                             format(reverse_domain.name))

    return redirect('/mozdns/reverse_domain/')
