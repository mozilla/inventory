import csv

from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, InvalidPage, EmptyPage

from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import simplejson as json
import _mysql_exceptions

from systems.models import System, Location
from user_systems.models import UnmanagedSystem
from middleware.restrict_to_remote import allow_anyone

import re
from django.test.client import Client
from django.db.models import Q
from forms import ReportForm
import csv
from django.template.defaulttags import URLNode
from django.conf import settings
from jinja2.filters import contextfilter
from django.utils import translation
from libs.jinja import jinja_render_to_response
@allow_anyone
def report_home(request):
    data = {}
    systems = None
    initial = {
            'system_type': ['SYSTEM'],
            'location': ['-1'],
            'system_status': ['-1'],


            }
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            search_q = Q()
            allocation = request.POST.get('allocation', '')
            server_models = request.POST.get('server_models', '')
            operating_system = request.POST.get('operating_system', '')
            system_status = request.POST.getlist('system_status')
            location = request.POST.get('location')
            systems = System.objects.all()
            if 'SYSTEM' in request.POST.getlist('system_type'):
                if location:
                    if '-1' not in request.POST.getlist('location'):
                        for location in request.POST.getlist('location'):
                            search_q |= Q(system_rack__location__id=location)
                        total_count = System.with_related.filter(search_q).count()
                        systems = systems.filter(search_q)

                if allocation != '':
                    systems = systems.filter(Q(allocation=allocation))

                if server_models != '':
                    systems = systems.filter(Q(server_model__model__icontains=server_models)|Q(server_model__vendor__icontains=server_models))

                if operating_system != '':
                    systems = systems.filter(Q(operating_system__name__icontains=operating_system)|Q(operating_system__version__icontains=operating_system))

                if '-1' not in system_status:
                    the_query = Q()
                    for ss in system_status:
                        the_query |= Q(system_status__id=ss)
                    systems = systems.filter(the_query)
            total_count = systems.count()
            if 'UNMANAGED' in request.POST.getlist('system_type'):
                pass
            data['content'] = str(total_count)
            if 'CSV' == request.POST['output']:
                response = HttpResponse(mimetype='text/csv')
                response['Content-Disposition'] = 'attachment; inventory_report.csv'
                writer = csv.writer(response)
                columns = [
                        'Hostname',
                        'Asset Tag',
                        'Purchase Date',
                        'Server Model',
                        'Serial',
                        'Purchase Price',
                        'Operating System',
                        'Location',
                        ]
                writer.writerow(columns)
                for system in systems: 
                    writer.writerow([
                    system.hostname,
                    system.asset_tag, 
                    system.purchase_date,
                    system.server_model,
                    system.serial,
                    system.purchase_price,
                    system.operating_system if system.operating_system else '',
                    system.system_rack.location if system.system_rack else '',
                    ])
                return response
            if 'SCREEN' == request.POST['output']:
                template = 'reports/index.html'
                for system in systems:
                    for column in columns:
                        pass
        else:
            form = ReportForm(request.POST)
            data['form'] = form
            template = 'reports/index.html'
    else:
        form = ReportForm(initial=initial)
        data['form'] = form
        template = 'reports/index.html'

    return jinja_render_to_response(template, {
            'systems': systems,
            'form': form
           })
