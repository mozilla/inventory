from django.views.decorators.csrf import csrf_exempt
import csv
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, InvalidPage, EmptyPage

from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import  redirect, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import translation

import _mysql_exceptions

import models
from middleware.restrict_to_remote import allow_anyone,sysadmin_only, LdapGroupRequired

import re
from django.test.client import RequestFactory
from jinja2.filters import contextfilter

import models
from libs.jinja import render_to_response as render_to_response
from middleware.restrict_to_remote import allow_anyone,sysadmin_only, LdapGroupRequired
from Rack import Rack
from MozInvAuthorization.KeyValueACL import KeyValueACL 
from core.interface.static_intr.models import StaticInterface
import simplejson as json
from mozdns.utils import ensure_label_domain, prune_tree


# Import resources
from api_v2.dhcp_handler import DHCPHandler
from api_v2.keyvalue_handler import KeyValueHandler


# Use this object to generate request objects for calling tastypie views
factory = RequestFactory()

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

def check_dupe_nic(request,system_id, adapter_number):
    try:
        system = models.System.objects.get(id=system_id)
        found = system.check_for_adapter(adapter_number)
    except:
        pass
    return HttpResponse(found)

def check_dupe_nic_name(requessdft,system_id,adapter_name):
    try:
        system = models.System.objects.get(id=system_id)
        found = system.check_for_adapter_name(adapter_name)
    except:
        pass
    return HttpResponse(found)

@allow_anyone
def system_rack_elevation(request, rack_id):
    r = Rack(rack_id)
    data  = {
            'rack_ru': r.ru,
            'ethernet_patch_panels_24': r.ethernet_patch_panel_24,
            'ethernet_patch_panels_48': r.ethernet_patch_panel_48,
            'systems': r.systems,
    }
    data = json.dumps(data)
    return render_to_response('systems/rack_elevation.html', {
        'data':data,
        },
        RequestContext(request))


def get_next_intr_name(request, system_pk):
    system = get_object_or_404(models.System, pk=system_pk)
    interface_type, primary, alias = system.get_next_adapter()
    return HttpResponse(json.dumps({'success': True,
        'intr_name': "{0}{1}.{2}".format(interface_type, primary, alias)}))

@csrf_exempt
def create_adapter(request, system_id):
    if not request.POST.get('is_ajax', False):
        return HttpResponse("Ajax only homie.")

    from api_v3.system_api import SystemResource
    from mozdns.view.models import View
    system = get_object_or_404(models.System, id=system_id)
    ip_address = request.POST.get('ip_address', '')
    mac_address = request.POST.get('mac_address', '')
    intr_name = request.POST.get('interface', '')

    # Determine whether to enable or disable DNS and DHCP
    if request.POST.get('enable_dhcp', '') == 'false':
        enable_dhcp = False
    else:
        enable_dhcp = True
    if request.POST.get('enable_dns', '') == 'false':
        enable_dns = False
    else:
        enable_dns = True

    # Determine which DNS views to to enable. (Won't matter if DNS is not
    # enabled)
    if request.POST.get('enable_public', '') == 'false':
        enable_public = False
    else:
        enable_public = True

    if request.POST.get('enable_private', '') == 'false':
        enable_private = False
    else:
        enable_private = True

    if not intr_name:
        return HttpResponse(json.dumps({'success': False, 'error_message':
            "Please specify a interface name or select to have the name "
            "automatically generated."}))

    # Figure out label and domain
    fqdn = request.POST.get('fqdn', '')
    try:
        label, domain = ensure_label_domain(fqdn)
        # If we hit we need to back out of creating this interface,
        # make sure to call prune_tree on this domain.
    except ValidationError, e:
        return HttpResponse(json.dumps({'success': False,
            'error_message': "Error creating label and domain: "
            "{0}".format(" ".join(e.messages))}))

    # Determine the keys to store later when nameing the interface.
    try:
        x = SystemResource.extract_nic_attrs(intr_name)
        interface_type, primary, alias = x
    except ValidationError, e:
        prune_tree(domain)
        return HttpResponse(json.dumps({'success': False, 'error_message':
            " ".join(e.messages)}))

    # Create the Interface
    s = StaticInterface(label=label, mac=mac_address, domain=domain,
        ip_str=ip_address, ip_type='4', system=system,
        dhcp_enabled=enable_dhcp, dns_enabled=enable_dns)
    try:
        s.clean()
        s.save()
    except ValidationError, e:
        prune_tree(domain)
        return HttpResponse(json.dumps({'success': False, 'error_message':
            "Failed to create an interface: {0}".format(" ".join(e.messages))}))

    # Configure views
    if enable_dns:
        if enable_public:
            public = View.objects.get(name='public')
            s.views.add(public)
        if enable_private:
            private = View.objects.get(name='private')
            s.views.add(private)
        s.save()


    # Add key value pairs
    s.update_attrs()
    try:
        s.attrs.primary = primary
        s.attrs.interface_type = interface_type
        s.attrs.alias = alias
    except AttributeError, e:
        return HttpResponse(json.dumps({'success': True, 'error_message':
            "The Interface was created but there were other errors: ".join(
                e.messages)}))

    return HttpResponse(json.dumps({'success': True}))


@allow_anyone
def system_auto_complete_ajax(request):
    query = request.GET['query']
    system_list = models.System.objects.filter(hostname__icontains=query)
    hostname_list = [system.hostname for system in system_list]
    id_list = [system.id for system in system_list]
    ret_dict = {}
    ret_dict['query'] = query
    ret_dict['suggestions'] = hostname_list
    ret_dict['data'] = id_list
    return HttpResponse(json.dumps(ret_dict))

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
        if search_term.startswith('/') and len(search_term) > 1:
            try:
                search_term = search_term[1:]
                search_q = Q(hostname__regex=search_term)
            except:
                search_q = Q(hostname__icontains=search_term)
        else:
            search_q = Q(hostname__icontains=search_term)
        search_q |= Q(serial__icontains=search_term)
        search_q |= Q(notes__icontains=search_term)
        search_q |= Q(asset_tag=search_term)
        search_q |= Q(oob_ip__icontains=search_term)
        search_q |= Q(keyvalue__value__icontains=search_term)
        try:
            total_count = models.System.with_related.filter(search_q).distinct('hostname').count()
        except:
            total_count = 0
        end_display = int(iDisplayStart) + int(iDisplayLength)
        try:
            systems = models.System.with_related.filter(search_q).order_by('hostname').distinct('hostname')[iDisplayStart:end_display]
            the_data = build_json(request, systems, sEcho, total_count, iDisplayLength, sort_col, sort_dir)
        except:
            the_data = '{"sEcho": %s, "iTotalRecords":0, "iTotalDisplayRecords":0, "aaData":[]}' % (sEcho) 
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


#@ldap_group_required('build')
#@LdapGroupRequired('build_team', exclusive=False)
@allow_anyone
def home(request):
    """Index page"""
    return render_to_response('systems/index.html', {
            'read_only': getattr(request, 'read_only', False),
            #'is_build': getattr(request.user.groups.all(), 'build', False),
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
    matches = re.search('^nic\.(\d+)', str(kv.key) )
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
@csrf_exempt
def save_key_value(request, id):
    system_id = None
    validated = True
    resp = {'success': True, 'errorMessage' : ''}
    post_key = request.POST.get('key').strip()
    post_value = request.POST.get('value').strip()
    """
        Create the key value acl object.
        We can use it to validate based on criteria below
    """
    try:
        tmp = models.KeyValue.objects.get(id=id)
        system = tmp.system
    except Exception, e:
        print e
        pass

        
    acl = KeyValueACL(request)
    if post_key == 'shouldfailvalidation':
        resp['success'] = False
        resp['errorMessage'] = 'Validation Failed'
        validated = False
    kv = models.KeyValue.objects.get(id=id)
    if kv is not None and validated:
        ##Here we eant to check if the existing key is a network adapter. If so we want to find out if it has a dhcp scope. If so then we want to add it to ScheduledTasks so that the dhcp file gets regenerated
        matches = re.search('^nic\.(\d+)', str(kv.key).strip() )
        """
            Check to see if we have a network adapter
            If so we need to flag the dhcp zone file to be regenerated
        """
        if matches and matches.group(1):
            """
                Check to see if it's an ipv4_address key
                run KeyValueACL.check_ip_not_exist_other_system
            """
            #import pdb; pdb.set_trace()
            if re.search('^nic\.(\d+)\.ipv4_address', str(post_key).strip() ):
                try:
                    acl.check_ip_not_exist_other_system(system, post_value)
                except Exception, e:
                    resp['success'] = False
                    resp['errorMessage'] = str(e)
                    return HttpResponse(json.dumps(resp))
            try:
                existing_dhcp_scope = models.KeyValue.objects.filter(system=kv.system).filter(key='nic.%s.dhcp_scope.0' % matches.group(1))[0].value
                if existing_dhcp_scope is not None:
                    models.ScheduledTask(task=existing_dhcp_scope, type='dhcp').save()
            except Exception, e: 
                pass
            try:
                existing_reverse_dns_zone = models.KeyValue.objects.filter(system=kv.system).filter(key='nic.%s.reverse_dns_zone.0' % matches.group(1))[0].value
                if existing_reverse_dns_zone is not None:
                    models.ScheduledTask(task=existing_reverse_dns_zone, type='reverse_dns_zone').save()
            except Exception, e: 
                pass
        try:
            kv.key = request.POST.get('key').strip()
            kv.value = request.POST.get('value').strip()
            system_id = str(kv.system_id)
            kv.save()
        except:
            kv.key = None
            kv.value = None
        ##Here we eant to check if the new key is a network adapter. If so we want to find out if it has a dhcp scope. If so then we want to add it to ScheduledTasks so that the dhcp file gets regenerated
        if kv.key is not None:
            matches = re.search('nic\.(\d+)', kv.key)
            if matches and matches.group(1):
                new_dhcp_scope = None
                new_reverse_dns_zone = None
                try:
                    new_dhcp_scope = models.KeyValue.objects.filter(system=kv.system).filter(key='nic.%s.dhcp_scope.0' % matches.group(1))[0].value
                except Exception, e:
                    pass

                try:
                    new_reverse_dns_zone = models.KeyValue.objects.filter(system=kv.system).filter(key='nic.%s.reverse_dns_zone.0' % matches.group(1))[0].value
                except Exception, e:
                    pass
                if new_dhcp_scope is not None:
                    try:
                        models.ScheduledTask(task=new_dhcp_scope, type='dhcp').save()
                    except Exception, e:
                        print e
                        ##This is due to the key already existing in the db
                        pass
                if new_reverse_dns_zone is not None:
                    try:
                        models.ScheduledTask(task=new_reverse_dns_zone, type='reverse_dns_zone').save()
                    except Exception ,e:
                        print e
                        ##This is due to the key already existing in the db
                        pass


    return HttpResponse(json.dumps(resp));
    #return HttpResponseRedirect('/en-US/systems/get_key_value_store/' + system_id + '/')

@csrf_exempt
def create_key_value(request, id):
    system = models.System.objects.get(id=id)
    key = 'None'
    value = 'None'
    print request.POST
    if 'key' in request.POST:
        key = request.POST['key'].strip()
    if 'value' in request.POST:
        value = request.POST['value'].strip()
    kv = models.KeyValue(system=system,key=key,value=value)
    print "Key is %s: Value is %s." % (key, value)
    kv.save();
    matches = re.search('^nic\.(\d+)', str(kv.key) )
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
    if system.notes:
        system.notes = system.notes.replace("\n", "<br />")
    show_nics_in_key_value = False
    is_release = False
    try:
        request = factory.get('/api/v2/keyvalue/3/',
                {'key_type':'adapters_by_system','system':system.hostname})
        h = KeyValueHandler()
        adapters = h.read(request, key_value_id='3')
    except:
        adapters = []
    if system.allocation is 'release':
        is_release = True
    if (system.serial and
            system.server_model and
            system.server_model.part_number and
            system.server_model.vendor == "HP"):

        system.warranty_link = "http://www11.itrc.hp.com/service/ewarranty/warrantyResults.do?productNumber=%s&serialNumber1=%s&country=US" % (system.server_model.part_number, system.serial)
    if show_nics_in_key_value:
        key_values = system.keyvalue_set.all()
    else:
        key_values = system.keyvalue_set.exclude(key__istartswith='nic.')

    intrs = StaticInterface.objects.filter(system = system)

    return render_to_response('systems/system_show.html', {
            'system': system,
            'interfaces': intrs,
            'adapters': adapters,
            'key_values': key_values,
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
    from forms import SystemForm
    if request.method == 'POST':
        form = SystemForm(request.POST, instance=instance)
        if form.is_valid():
            s = form.save(commit=False)
            s.save(request=request)
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

@csrf_exempt
def system_edit(request, id):
    system = get_object_or_404(models.System, pk=id)
    dhcp_scopes = None
    try:
        h = DHCPHandler()
        dhcp_scopes = h.read(request, dhcp_scope='phx-vlan73', dhcp_action='get_scopes_with_names')
    except Exception, e:
        print e
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
        system = models.System.objects.get(id=system_id)
        request = factory.get('/api/v2/keyvalue/3/',
                {'key_type':'adapters_by_system','system':system.hostname})
        h = KeyValueHandler()
        request = factory.get('/api/keyvalue/?keystore=%s' % (system.hostname), follow=True)
        resp = json.dumps(h.read(request, key_value_id='3'))
        return_obj = resp.replace(",",",<br />")
    except:
        return_obj = 'This failed'
    return HttpResponse(return_obj)


    
def new_rack_system_ajax(request, rack_id):
    from forms import RackSystemForm
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
def racks_by_location(request, location=0):
    ret_list = []
    if int(location) > 0:
        location = models.Location.objects.get(id=location)
        racks = models.SystemRack.objects.select_related('location').filter(location=location).order_by('name')
    else:
        racks = models.SystemRack.objects.select_related('location').order_by('location', 'name')

    for r in racks:
        ret_list.append({'name':'%s %s' % (r.location.name, r.name), 'id':r.id})
    return HttpResponse(json.dumps(ret_list))

@allow_anyone
def racks(request):
    from forms import RackFilterForm
    filter_form = RackFilterForm(request.GET)

    racks = models.SystemRack.objects.select_related('location')

    system_query = Q()
    if 'location' in request.GET:
        location_id = request.GET['location']
        has_query = True
        if len(location_id) > 0 and int(location_id) > 0:
            loc = models.Location.objects.get(id=location_id)
            filter_form.fields['rack'].choices = [('','ALL')] + [(m.id, m.location.name + ' ' +  m.name) for m in models.SystemRack.objects.filter(location=loc).order_by('name')]
    else:
        has_query = False
    if filter_form.is_valid():

        if filter_form.cleaned_data['rack']:
            racks = racks.filter(id=filter_form.cleaned_data['rack'])
            has_query = True
        if filter_form.cleaned_data['location'] and int(filter_form.cleaned_data['location']) > 0:
            racks = racks.filter(location=filter_form.cleaned_data['location'])
            has_query = True
        if filter_form.cleaned_data['allocation']:
            system_query &= Q(allocation=filter_form.cleaned_data['allocation'])
            has_query = True
        if filter_form.cleaned_data['status']:
            system_query &= Q(system_status=filter_form.cleaned_data['status'])
            has_query = True
    ##Here we create an object to hold decommissioned systems for the following filter
    if not has_query:
        racks = []
    else:
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


def rack_delete(request, object_id):
    from models import SystemRack
    rack = get_object_or_404(SystemRack, pk=object_id)
    if request.method == "POST":
        rack.delete()
        return HttpResponseRedirect('/systems/racks/')
    else:
        return render_to_response('systems/rack_confirm_delete.html', {
                'rack': rack,
            },
            RequestContext(request))


def rack_edit(request, object_id):
    rack = get_object_or_404(models.SystemRack, pk=object_id)
    from forms import SystemRackForm
    initial = {}
    if request.method == 'POST':
        form = SystemRackForm(request.POST, instance=rack)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/systems/racks/')
    else:
        form = SystemRackForm(instance=rack)

    return render_to_response(
        'systems/generic_form.html',
        {
            'form': form,
        },
        RequestContext(request))


def rack_new(request):
    from forms import SystemRackForm
    initial = {}
    if request.method == 'POST':
        form = SystemRackForm(request.POST, initial=initial)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/systems/racks/')
    else:
        form = SystemRackForm(initial=initial)

    return render_to_response(
        'generic_form.html',
        {
            'form': form,
        },
        RequestContext(request))


def location_show(request, object_id):
    object = get_object_or_404(models.Location, pk=object_id)

    return render_to_response(
        'systems/location_detail.html',
        {
            'object': object,
        },
        RequestContext(request))


def location_edit(request, object_id):
    location = get_object_or_404(models.Location, pk=object_id)
    from forms import LocationForm
    initial = {}
    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/systems/locations/')
    else:
        form = LocationForm(instance=location)

    return render_to_response(
        'generic_form.html',
        {
            'form': form,
        },
        RequestContext(request))


def location_new(request):
    from forms import LocationForm
    initial = {}
    if request.method == 'POST':
        form = LocationForm(request.POST, initial=initial)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/systems/locations/')
    else:
        form = LocationForm(initial=initial)

    return render_to_response(
        'generic_form.html',
        {
            'form': form,
        },
        RequestContext(request))


def server_model_edit(request, object_id):
    server_model = get_object_or_404(models.ServerModel, pk=object_id)
    from forms import ServerModelForm
    initial = {}
    if request.method == 'POST':
        form = ServerModelForm(request.POST, instance=server_model)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/systems/server_models/')
    else:
        form = ServerModelForm(instance=server_model)

    return render_to_response(
        'generic_form.html',
        {
            'form': form,
        },
        RequestContext(request))


@csrf_exempt
def operating_system_create_ajax(request):
    if request.method == "POST":
        if 'name' in request.POST and 'version' in request.POST:
            name = request.POST['name']
            version = request.POST['version']
        models.OperatingSystem(name=name, version=version).save()
        return operating_system_list_ajax(request)
    else:
        return HttpResponse("OK")


@csrf_exempt
def server_model_create_ajax(request):
    if request.method == "POST":
        if 'model' in request.POST and 'vendor' in request.POST:
            model = request.POST['model']
            vendor = request.POST['vendor']
        models.ServerModel(vendor=vendor, model=model).save()
        return server_model_list_ajax(request)
    else:
        return HttpResponse("OK")


def operating_system_list_ajax(request):
    ret = []
    for m in models.OperatingSystem.objects.all():
        ret.append({'id': m.id, 'name': "%s - %s" % (m.name, m.version)})

    return HttpResponse(json.dumps(ret))


def server_model_list_ajax(request):
    ret = []
    for m in models.ServerModel.objects.all():
        ret.append({'id': m.id, 'name': "%s - %s" % (m.vendor, m.model)})

    return HttpResponse(json.dumps(ret))


def server_model_show(request, object_id):
    object = get_object_or_404(models.ServerModel, pk=object_id)

    return render_to_response(
        'systems/servermodel_detail.html',
        {
            'object': object,
        },
        RequestContext(request))


def server_model_list(request):
    object_list = models.ServerModel.objects.all()
    return render_to_response(
        'systems/servermodel_list.html',
        {
            'object_list': object_list,
        },
        RequestContext(request))


def allocation_show(request, object_id):
    object = get_object_or_404(models.Allocation, pk=object_id)

    return render_to_response(
        'systems/allocation_detail.html',
        {
            'object': object,
        },
        RequestContext(request))


def allocation_edit(request, object_id):
    allocation = get_object_or_404(models.Allocation, pk=object_id)
    from forms import AllocationForm
    initial = {}
    if request.method == 'POST':
        form = AllocationForm(request.POST, instance=allocation)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/systems/allocations/')
    else:
        form = AllocationForm(instance=allocation)

    return render_to_response(
        'generic_form.html',
        {
            'form': form,
        },
        RequestContext(request))


def allocation_list(request):
    object_list = models.Allocation.objects.all()
    return render_to_response(
        'systems/allocation_list.html',
        {
            'object_list': object_list,
        },
        RequestContext(request))


def allocation_new(request):
    from forms import AllocationForm
    initial = {}
    if request.method == 'POST':
        form = AllocationForm(request.POST, initial=initial)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/systems/allocations/')
    else:
        form = AllocationForm(initial=initial)

    return render_to_response(
        'generic_form.html',
        {
            'form': form,
        },
        RequestContext(request))


def location_list(request):
    object_list = models.Location.objects.all()
    return render_to_response(
        'systems/location_list.html',
        {
            'object_list': object_list,
        },
        RequestContext(request))


def csv_import(request):
    from forms import CSVImportForm

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

                system_data = dict(
                    (a, getter(cur_data.get(a, None)))
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

    return render_to_response(
        'systems/csv_import.html',
        {
            'form': form,
            'allowed_columns': ALLOWED_COLUMNS,
            'new_systems': new_systems,
        },
        RequestContext(request))
