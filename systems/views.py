import csv

from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, InvalidPage, EmptyPage

from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import  redirect, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import simplejson as json
import _mysql_exceptions

import models
from forms import RackFilterForm, SystemForm, RackSystemForm, CSVImportForm
from middleware.restrict_to_remote import allow_anyone

import re
from django.test.client import Client
from jinja2.filters import contextfilter
from django.utils import translation
from libs.jinja import render_to_response
from django.views.decorators.csrf import csrf_exempt
# Source: http://nedbatchelder.com/blog/200712/human_sorting.html
# Author: Ned Batchelder
def tryint(s):
    try:
        return int(s)
    except:
        return s

def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    return [ tryint(c) for c in re.split('([0-9]+)', s) ]

def sort_nicely(l):
    """ Sort the given list in the way that humans expect.
    """
    l.sort(key=alphanum_key)
def parse_title_num(title):
   val = 0
   try:
      val = int(title.rsplit('#')[-1])
   except ValueError:
      pass
   return val

def check_dupe_nic(request,system_id,adapter_number):
    try:
        system = models.System.objects.get(id=system_id)
        found = system.check_for_adapter(adapter_number)
    except:
        pass
    return HttpResponse(found)
def check_dupe_nic_name(request,system_id,adapter_name):
    try:
        system = models.System.objects.get(id=system_id)
        found = system.check_for_adapter_name(adapter_name)
    except:
        pass
    return HttpResponse(found)
@allow_anyone
def list_all_systems_ajax(request):
#iSortCol_0 = which column is sorted
#sSortDir_0 = which direction 	
    
    cols = ['hostname','serial','asset_tag','server_model','system_rack', 'oob_ip', 'system_status']
    sort_col = cols[0]
    if 'iSortCol_0' in request.GET:
        sort_col = cols[int(request.GET['iSortCol_0'])]

    sort_dir = 'asc'
    if 'sSortDir_0' in request.GET:
        sort_dir = request.GET['sSortDir_0']


    if 'sEcho' in request.GET:
        sEcho = request.GET['sEcho']

    if 'sSearch' in request.GET and request.GET['sSearch'] > '':
        search_term = request.GET['sSearch']
    else:
        search_term = None

    if 'iDisplayLength' in request.GET and request.GET['iDisplayLength'] > '':
        iDisplayLength = request.GET['iDisplayLength']
    else:
        iDisplayLength = 100

    if 'iDisplayStart' in request.GET and request.GET['iDisplayStart'] > '':
        iDisplayStart = request.GET['iDisplayStart']
    else:
        iDisplayStart = 0

    if search_term is None:
        end_display = int(iDisplayStart) + int(iDisplayLength)
        system_count = models.System.objects.all().count()
        systems = models.System.objects.all()[iDisplayStart:end_display]
        the_data = build_json(request, systems, sEcho, system_count, iDisplayLength, sort_col, sort_dir)

    if search_term is not None and len(search_term) > 0:
				
        search_q = Q(hostname__icontains=search_term)
        search_q |= Q(serial__contains=search_term)
        search_q |= Q(notes__contains=search_term)
        search_q |= Q(asset_tag=search_term)
        search_q |= Q(oob_ip__contains=search_term)
        total_count = models.System.with_related.filter(search_q).count()
        end_display = int(iDisplayStart) + int(iDisplayLength)
        systems = models.System.with_related.filter(search_q).order_by('hostname')[iDisplayStart:end_display]
        the_data = build_json(request, systems, sEcho, total_count, iDisplayLength, sort_col, sort_dir)
    return HttpResponse(the_data)

def build_json(request, systems, sEcho, total_records, display_count, sort_col, sort_dir):
    system_list = []
    for system in systems:
        if system.serial is not None:
            serial = system.serial.strip()
        else:
            serial = ''

        if system.server_model is not None:
            server_model = str(system.server_model)
        else:
            server_model = ''
        if system.system_rack is not None:
            system_rack = "%s - %s" % (str(system.system_rack), system.rack_order)
            system_rack_id = str(system.system_rack.id)
        else:
            system_rack = ''
            system_rack_id = ''

        if system.system_status is not None:
            system_status = str(system.system_status)
        else:
            system_status = ''

        if system.asset_tag is not None:
            asset_tag = system.asset_tag.strip()
        else:
            asset_tag = ''
        if system.oob_ip is not None:
            oob_ip = system.oob_ip.strip()
        else:
            oob_ip = ''

        ro = getattr(request, 'read_only', False)
        if ro:
            system_id = 0
        else:
            system_id = system.id

        system_list.append({'hostname': system.hostname.strip(), 'oob_ip': oob_ip, 'serial': serial, 'asset_tag': asset_tag, 'server_model': server_model,
        'system_rack':system_rack, 'system_status':system_status, 'id':system_id, 'system_rack_id': system_rack_id})

    the_data = '{"sEcho": %s, "iTotalRecords":0, "iTotalDisplayRecords":0, "aaData":[]}' % (sEcho)

    #try:
    if len(system_list) > 0:
        system_list.sort(key=lambda x: alphanum_key(x[sort_col]))
        if sort_dir == 'desc':
            #system_list = system_list.reverse()
            system_list.reverse()


        #the_data = '{"sEcho": %s, "iTotalRecords":%i, "iTotalDisplayRecords":%s, "aaData":[' % (sEcho,  total_records, display_count)
        the_data = '{"sEcho": %s, "iTotalRecords":%i, "iTotalDisplayRecords":%i, "aaData":[' % (sEcho,  total_records, total_records)
        #sort_nicely(system_list)
        counter = 0
        for system in system_list:
            if counter < display_count:
                the_data += '["%i,%s","%s","%s","%s","%s,%s", "%s", "%s", "%i"],' % (system['id'],system['hostname'], system['serial'],system['asset_tag'],system['server_model'],system['system_rack_id'], system['system_rack'], system['oob_ip'], system['system_status'], system['id'])
                counter += 1
            else:
                counter = display_count
        the_data = the_data[:-1]
        the_data += ']}'
    #except:
        pass
    
    return the_data 


@allow_anyone
def home(request):
    """Index page"""
    system_list = models.System.with_related.order_by('hostname')
    paginator = Paginator(system_list, 100)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        systems = paginator.page(page)
    except (EmptyPage, InvalidPage):
        systems = paginator.page(paginator.num_pages)


    return render_to_response('systems/index.html', {
            'systems': systems,
            'read_only': getattr(request, 'read_only', False),
           })

@allow_anyone
def system_quicksearch_ajax(request):
    """Returns systems sort table"""
    search_term = request.POST['quicksearch']
    search_q = Q(hostname__icontains=search_term)
    search_q |= Q(serial__contains=search_term)
    search_q |= Q(notes__contains=search_term)
    search_q |= Q(asset_tag=search_term)
    systems = models.System.with_related.filter(search_q).order_by('hostname')
    if 'is_test' not in request.POST:
        return render_to_response('systems/quicksearch.html', {
                'systems': systems,
                'read_only': getattr(request, 'read_only', False),
            },
            RequestContext(request))
    else:
        from django.core import serializers
        systems_data = serializers.serialize("json", systems)
        return HttpResponse(systems_data)

def get_key_value_store(request, id):
    system = models.System.objects.get(id=id)
    key_value_store = models.KeyValue.objects.filter(system=system)
    return render_to_response('systems/key_value_store.html', {
            'key_value_store': key_value_store,
           },
           RequestContext(request))
def delete_key_value(request, id, system_id):
    kv = models.KeyValue.objects.get(id=id)
    matches = re.search('^nic\.(\d+)', kv.key)
    if matches:
        try:
            existing_dhcp_scope = models.KeyValue.objects.filter(system=kv.system).filter(key='nic.%s.dhcp_scope.0' % matches.group(1))[0].value
            models.ScheduledTask(task=existing_dhcp_scope, type='dhcp').save()
        except:
            pass
    kv.delete()
    system = models.System.objects.get(id=system_id)
    key_value_store = models.KeyValue.objects.filter(system=system)
    return render_to_response('systems/key_value_store.html', {
            'key_value_store': key_value_store,
           },
           RequestContext(request))
def save_key_value(request, id):
    kv = models.KeyValue.objects.get(id=id)
    if kv is not None:
        ##Here we eant to check if the existing key is a network adapter. If so we want to find out if it has a dhcp scope. If so then we want to add it to ScheduledTasks so that the dhcp file gets regenerated
        matches = re.search('^nic\.(\d+)', kv.key)
        if matches:
            try:
                existing_dhcp_scope = models.KeyValue.objects.filter(system=kv.system).filter(key='nic.%s.dhcp_scope.0' % matches.group(1))[0].value
                existing_reverse_dns_zone = models.KeyValue.objects.filter(system=kv.system).filter(key='nic.%s.reverse_dns_zone.0' % matches.group(1))[0].value
                if existing_dhcp_scope is not None:
                    models.ScheduledTask(task=existing_dhcp_scope, type='dhcp').save()
                if existing_reverse_dns_zone is not None:
                    models.ScheduledTask(task=existing_reverse_dns_zone, type='reverse_dns_zone').save()
            except:
                pass
        kv.key = request.POST['key'].strip()
        kv.value = request.POST['value'].strip()
        system_id = str(kv.system_id)
        kv.save()
        ##Here we eant to check if the new key is a network adapter. If so we want to find out if it has a dhcp scope. If so then we want to add it to ScheduledTasks so that the dhcp file gets regenerated
        matches = re.search('nic\.(\d+)', kv.key)
        if matches.group(1):
            try:
                new_dhcp_scope = models.KeyValue.objects.filter(system=kv.system).filter(key='nic.%s.dhcp_scope.0' % matches.group(1))[0].value
                new_reverse_dns_zone = models.KeyValue.objects.filter(system=kv.system).filter(key='nic.%s.reverse_dns_zone.0' % matches.group(1))[0].value
            except:
                new_dhcp_scope = None
            if new_dhcp_scope:
                try:
                    models.ScheduledTask(task=new_dhcp_scope, type='dhcp').save()
                    models.ScheduledTask(task=new_reverse_dns_zone, type='reverse_dns_zone').save()
                except:
                    ##This is due to the key already existing in the db
                    pass


    return HttpResponseRedirect('/systems/get_key_value_store/' + system_id + '/')

def create_key_value(request, id):
    system = models.System.objects.get(id=id)
    key = 'None'
    value = 'None'
    if 'key' in request.POST:
        key = request.POST['key'].strip()
    if 'value' in request.POST:
        value = request.POST['value'].strip()
    kv = models.KeyValue(system=system,key=key,value=value)
    kv.save();
    matches = re.search('^nic\.(\d+)', kv.key)
    if matches:
        try:
            existing_dhcp_scope = models.KeyValue.objects.filter(system=kv.system).filter(key='nic.%s.dhcp_scope.0' % matches.group(1))[0].value
            models.ScheduledTask(task=existing_dhcp_scope, type='dhcp').save()
        except:
            pass
    key_value_store = models.KeyValue.objects.filter(system=system)
    return render_to_response('systems/key_value_store.html', {
            'key_value_store': key_value_store,
           },
           RequestContext(request))
def get_network_adapters(request, id):
    adapters = models.NetworkAdapter.objects.filter(system_id=id)
    return render_to_response('systems/network_adapters.html', {
            'adapters': adapters,
            'switches': models.System.objects.filter(is_switch=1),
            'dhcp_scopes': models.DHCP.objects.all()
            #'read_only': getattr(request, 'read_only', False),
           },
           RequestContext(request))
def delete_network_adapter(request, id, system_id):
    adapter = models.NetworkAdapter.objects.get(id=id)
    adapter.delete()
    adapters = models.NetworkAdapter.objects.filter(system_id=system_id)
    return render_to_response('systems/network_adapters.html', {
            'adapters': adapters,
            'dhcp_scopes': models.DHCP.objects.all(),
            'switches': models.System.objects.filter(is_switch=1)
            #'read_only': getattr(request, 'read_only', False),
           },
           RequestContext(request))

def create_network_adapter(request, id):

    nic = models.NetworkAdapter(system_id=id)
    nic.save()
    adapters = models.NetworkAdapter.objects.filter(system_id=id)
    return render_to_response('systems/network_adapters.html', {
            'adapters': adapters,
            'dhcp_scopes': models.DHCP.objects.all(),
            'switches': models.System.objects.filter(is_switch=1)
            #'read_only': getattr(request, 'read_only', False),
           },
           RequestContext(request))

def save_network_adapter(request, id):
    import re
    nic = models.NetworkAdapter.objects.get(id=id)
    if nic is not None:
        mac = request.POST['mac_address']
        mac = mac.replace(':','').replace(' ','').replace('.','')
        tmp = mac[0:2] + ':' + mac[2:4] + ':' + mac[4:6] + ':' + mac[6:8] + ':' + mac[8:10] + ':' + mac[10:12]
        mac = tmp
        nic.dhcp_scope_id = request.POST['dhcp_scope_id']
        nic.mac_address = mac
        nic.ip_address = request.POST['ip_address']
        nic.filename = request.POST['filename']
        nic.option_host_name = request.POST['option_host_name']
        nic.option_domain_name = request.POST['option_domain_name']
        nic.adapter_name = request.POST['adapter_name']
        if request.POST['switch_id']:
            nic.switch_id = request.POST['switch_id']
        else:
            nic.switch_id = None
        nic.switch_port = request.POST['switch_port']
        nic.save()
    return HttpResponseRedirect('/systems/get_network_adapters/' + id)





@allow_anyone
def system_show(request, id):
    system = get_object_or_404(models.System, pk=id)
    is_release = False
    try:
        client = Client()
        adapters = json.loads(client.get('/api/v2/keyvalue/3/', {'key_type':'adapters_by_system','system':system.hostname}).content)
    except:
        adapters = []
    if system.allocation is 'release':
        is_release = True
    if (system.serial and
            system.server_model and
            system.server_model.part_number and
            system.server_model.vendor == "HP"):

        system.warranty_link = "http://www11.itrc.hp.com/service/ewarranty/warrantyResults.do?productNumber=%s&serialNumber1=%s&country=US" % (system.server_model.part_number, system.serial)

    return render_to_response('systems/system_show.html', {
            'system': system,
            'adapters': adapters,
            'is_release': is_release,
            'read_only': getattr(request, 'read_only', False),
           },
           RequestContext(request))

@allow_anyone
def system_show_by_asset_tag(request, id):
    system = get_object_or_404(models.System, asset_tag=id)
    is_release = True
    if system.allocation is 'release':
        is_release = True
    if (system.serial and
            system.server_model and
            system.server_model.part_number and
            system.server_model.vendor == "HP"):

        system.warranty_link = "http://www11.itrc.hp.com/service/ewarranty/warrantyResults.do?productNumber=%s&serialNumber1=%s&country=US" % (system.server_model.part_number, system.serial)

    return render_to_response('systems/system_show.html', {
            'system': system,
            'is_release': True,
            'read_only': getattr(request, 'read_only', False),
           },
           RequestContext(request))

def system_view(request, template, data, instance=None):
    if request.method == 'POST':
        form = SystemForm(request.POST, instance=instance)
        if form.is_valid():
            s = form.save()
            return redirect(system_show, s.pk)
    else:
        form = SystemForm(instance=instance)

    data['form'] = form

    return render_to_response(template, 
                data,
                request
            )
@csrf_exempt
def system_new(request):
    return system_view(request, 'systems/system_new.html', {})


def system_edit(request, id):
    system = get_object_or_404(models.System, pk=id)
    client = Client()
    dhcp_scopes = None
    try:
        dhcp_scopes = json.loads(client.get('/api/v2/dhcp/phx-vlan73/get_scopes_with_names/').content)
    except:
        pass

    return system_view(request, 'systems/system_edit.html', {
            'system': system,
            'dhcp_scopes':dhcp_scopes,
            'revision_history':models.SystemChangeLog.objects.filter(system=system).order_by('-id')
            }, system)


def system_delete(request, id):
    system = get_object_or_404(models.System, pk=id)
    system.delete()
    return redirect(home)


def system_csv(request):
    systems = models.System.objects.all().order_by('hostname')

    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=systems.csv'

    writer = csv.writer(response)
    writer.writerow(['Host Name', 'Serial', 'Asset Tag', 'Model', 'Allocation', 'Rack', 'Switch Ports', 'OOB IP'])
    for s in systems:
        try:
            writer.writerow([s.hostname, s.serial, s.asset_tag, s.server_model, s.allocation, s.system_rack, s.switch_ports, s.oob_ip])
        except:
            writer.writerow([s.hostname, s.serial, s.asset_tag, s.server_model, '', s.system_rack, s.switch_ports, s.oob_ip])
        

    return response

def system_releng_csv(request):
    systems = models.System.objects.filter(allocation=2).order_by('hostname')

    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=systems.csv'

    writer = csv.writer(response)
    writer.writerow(['id','hostname', 'switch_ports', 'oob_ip', 'system_rack', 'asset_tag', 'operating_system', 'rack_order'])
    for s in systems:
        writer.writerow([s.id, s.hostname, s.switch_ports, s.oob_ip, s.system_rack, s.asset_tag, s.operating_system, s.rack_order])

    return response

def get_expanded_key_value_store(request, system_id):
    try:
        from django.test.client import Client
        client = Client()
        system = models.System.objects.get(id=system_id)
        resp = client.get('/api/keyvalue/?keystore=%s' % (system.hostname))
        return_obj = resp.content.replace("\n","<br />")
    except:
        return_obj = 'This failed'
    return HttpResponse(return_obj)


    
def new_rack_system_ajax(request, rack_id):
    rack = get_object_or_404(models.SystemRack, pk=rack_id)

    data = {}
    resp_data = {}
    template = 'systems/rack_form_partial.html'
    if request.method == 'POST':
        rack_form = RackSystemForm(request.POST)
        if rack_form.is_valid():
            new_system = rack_form.save(commit=False)
            new_system.system_rack = rack
            new_system.save()

            data['system'] = new_system
            resp_data['success'] = True
            template = 'systems/rack_row_partial.html'
        else:
            resp_data['success'] = False
    else:
        rack_form = RackSystemForm()

    data['form'] = rack_form
    data['rack'] = rack

    resp_data['payload'] = render_to_string(template, data, RequestContext(request))

    return HttpResponse(json.dumps(resp_data), mimetype="application/json")


@allow_anyone
def racks(request):
    filter_form = RackFilterForm(request.GET)

    racks = models.SystemRack.objects.select_related('location')

    system_query = Q()
    if filter_form.is_valid():
        if filter_form.cleaned_data['location']:
            racks = racks.filter(location=filter_form.cleaned_data['location'])
        if filter_form.cleaned_data['rack']:
            racks = racks.filter(id=filter_form.cleaned_data['rack'])
        if filter_form.cleaned_data['allocation']:
            system_query &= Q(allocation=filter_form.cleaned_data['allocation'])
        if filter_form.cleaned_data['status']:
            system_query &= Q(system_status=filter_form.cleaned_data['status'])

    ##Here we create an object to hold decommissioned systems for the following filter
    decommissioned = models.SystemStatus.objects.get(status='decommissioned')
    racks = [(k, list(k.system_set.select_related(
        'server_model',
        'allocation',
        'system_status',
    ).filter(system_query).exclude(system_status=decommissioned).order_by('rack_order'))) for k in racks]

    return render_to_response('systems/racks.html', {
            'racks': racks,
            'filter_form': filter_form,
            'read_only': getattr(request, 'read_only', False),
           },
           RequestContext(request))


def csv_import(request):
    def generic_getter(field):
        return field

    def uppercase_getter(field):
        return field.upper()

    def allocation_getter(field):
        try:
            return models.Allocation.objects.get(name=field)
        except models.Allocation.DoesNotExist:
            return None

    def system_status_getter(field):
        try:
            return models.SystemStatus.objects.get(status=field)
        except models.SystemStatus.DoesNotExist:
            return

    def server_model_getter(field):
        try:
            return models.ServerModel.objects.get(id=field)
        except models.ServerModel.DoesNotExist:
            return

    def rack_getter(field):
        try:
            return models.SystemRack.objects.get(name=field)
        except models.SystemRack.DoesNotExist:
            return None

    ALLOWED_COLUMNS = {
        'hostname': generic_getter,
        'asset_tag': generic_getter,
        'serial': uppercase_getter,
        'notes': generic_getter,
        'oob_ip': generic_getter,
        'system_status': system_status_getter,
        'allocation': allocation_getter,
        'system_rack': rack_getter,
        'rack_order': generic_getter,
        'server_model': server_model_getter,
        'purchase_price': generic_getter,
    }

    new_systems = 0
    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_reader = csv.reader(form.cleaned_data['csv'])
            headers = csv_reader.next()
            for line in csv_reader:
                cur_data = dict(zip(headers, line))

                system_data = dict((a, getter(cur_data.get(a, None)))
                                        for a, getter in ALLOWED_COLUMNS.iteritems())

                s = models.System(**system_data)
                try:
                    s.full_clean()
                except ValidationError, e:
                    print e
                else:
                    s.save()
                    new_systems += 1
            form = None
    else:
        form = CSVImportForm()

    return render_to_response('systems/csv_import.html', {
        'form': form,
        'allowed_columns': ALLOWED_COLUMNS,
        'new_systems': new_systems,
        },
        RequestContext(request))