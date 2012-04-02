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
from mozilla_inventory.middleware.restrict_to_remote import allow_anyone

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
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            search_q = Q()
            if 'SYSTEM' in request.POST.getlist('system_type'):
                if 'location' in request.POST:
                    if '-1' not in request.POST.getlist('location'):
                        for location in request.POST.getlist('location'):
                            search_q |= Q(system_rack__location__id=location)
                        total_count = System.with_related.filter(search_q).count()
                        systems = System.with_related.filter(search_q)
                    if len(search_q.children) == 0:
                        total_count = System.objects.count()

            if 'UNMANAGED' in request.POST.getlist('system_type'):
                pass
            data['content'] = str(total_count)
            columns = [
                    ]
            if 'CSV' == request.POST['output']:
                response = HttpResponse(mimetype='text/csv')
                response['Content-Disposition'] = 'attachment; inventory_report.csv'
                writer = csv.writer(response)
                for system in systems: 
                    writer.writerow([
                    system.asset_tag, 
                    system.purchase_date,
                    system.server_model,
                    system.serial,
                    system.purchase_price,
                    system.system_rack.location,
                    system.hostname,
                    ])
                return response
            if 'SCREEN' == request.POST['output']:
                for system in systems:
                    for column in columns:
                        pass
    else:
        form = ReportForm()
        data['form'] = form
        template = 'reports/index.html'

    return jinja_render_to_response(template, {
            'form': form
           })
