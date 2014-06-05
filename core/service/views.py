from django.db import transaction
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.http import HttpResponse

from core.search.compiler.django_compile import search_type
from core.service.models import Service
from core.service.forms import ServiceForm
from core.views import (
    CoreListView, CoreCreateView, CoreUpdateView,
    CoreDeleteView
)
from systems.models import System

import simplejson as json


class ServiceView(object):
    model = Service
    queryset = Service.objects.all()
    form_class = ServiceForm


class ServiceDeleteView(ServiceView, CoreDeleteView):
    pass


class ServiceListView(ServiceView, CoreListView):
    template_name = 'service/service_list.html'


class ServiceUpdateView(ServiceView, CoreUpdateView):
    template_name = 'service/service_form.html'


class ServiceCreateView(ServiceView, CoreCreateView):
    template_name = 'service/service_form.html'


def service_detail(request, pk):
    service = get_object_or_404(Service, pk=pk)

    return render(request, 'service/service_detail.html', {
        'service': service
    })
