from django.db import transaction
from django.core.exceptions import ValidationError
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


def service_export(request):
    if request.method == 'POST':
        return HttpResponse(status=405)  # Method Not Allowed

    search = request.GET.get('search', '')

    if not search:
        return HttpResponse(
            {'errors': "Please query about a service to export"},
            status=400
        )

    services, error = search_type(search, 'SERVICE')

    if error:
        return HttpResponse(
            json.dumps({'errors': str(error)}), status=400
        )

    return HttpResponse(json.dumps({
        'services': Service.export_services(services)
    }))


def service_import(request):
    if request.method == 'GET':
        return HttpResponse(status=405)  # Method Not Allowed

    try:
        services_data = json.loads(request.raw_post_data)
    except ValueError, e:
        return HttpResponse(json.dumps({'errors': str(e)}), status=400)

    if 'services' not in services_data:
        return HttpResponse(json.dumps({
            'errors': "A dictionary containing the 'services' key is required"
        }), status=400)

    with transaction.commit_manually():
        try:
            Service.import_services(services_data['services'])
        except (
            ValidationError,
            ValueError,
            System.DoesNotExist,
            Service.DoesNotExist
        ), e:
            transaction.rollback()
            return HttpResponse(json.dumps({'errors': str(e)}), status=400)
        except Exception, e:
            transaction.rollback()
            return HttpResponse(json.dumps({'errors': str(e)}), status=500)

        transaction.commit()

    # return a 200 and something that will parse as valid json
    return HttpResponse('{}')
