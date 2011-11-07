from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, InvalidPage, EmptyPage

from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
try:
    import json
except:
    from django.utils import simplejson as json
import _mysql_exceptions

import models
import forms
from truth.models import KeyValue as TruthKeyValue, Truth
from systems.models import NetworkAdapter
#import adapters.dhcp
from middleware.restrict_to_remote import allow_anyone

from DHCP import DHCP
from django.test.client import Client
from django.template.defaulttags import URLNode
from django.conf import settings
from jinja2.filters import contextfilter
from django.utils import translation
from libs.jinja import jinja_render_to_response




def showall(request):
    dhcp_scopes = models.DHCP.objects.all()	
    client = Client()
    resp = client.get('/api/keyvalue/?key=is_dhcp_scope')
    obj = json.loads(resp.content)
    dhcp_scopes = []
    for key in obj.iterkeys():
        dhcp_scopes.append(key.split(":")[1])

    return jinja_render_to_response('dhcp/index.html', {
            'dhcp_scopes': dhcp_scopes,
           })

def new(request):
    error_message = ''
    if request.method == 'POST':
        form = forms.AddDHCPScopeForm(request.POST)
        if form.is_valid():
            truth_exists = False
            try:
                tmp = Truth.objects.get(name=form.cleaned_data['scope_name'])
                truth_exists = True
            except:
                pass
            if truth_exists is False: 
                t = Truth(name=form.cleaned_data['scope_name'], description=form.cleaned_data['scope_description'])
                t.save()
                k = TruthKeyValue(truth=t,key='is_dhcp_scope',value='True')
                k.save()
                return redirect('/dhcp/edit/%s' % t.name)
            else:
                error_message = 'DHCP Scope Exists'
    else:
        form = forms.AddDHCPScopeForm()

    return render_to_response('dhcp/new.html', {
            "form": form ,
            "error_message":error_message
           },
           RequestContext(request))
def override_file(request, dhcp_scope):
    if request.method == 'POST':
        form = forms.DHCPScopeOverrideForm(request.POST)
        if form.is_valid():
            do = models.DHCPOverride.objects.get(dhcp_scope=dhcp_scope)
            do.override_text = form.cleaned_data['override_text']
            do.save()
            #s = form.save()
            #return redirect('/dhcp/show/')
    else:
        try:
            do = models.DHCPOverride.objects.get(dhcp_scope=dhcp_scope)
        except:
            do = models.DHCPOverride(dhcp_scope=dhcp_scope)
            do.save()

        form = forms.DHCPScopeOverrideForm(initial={'dhcp_scope':dhcp_scope, 'override_text':do.override_text})

    return render_to_response('dhcp/override.html', {
            "form": form,
            'dhcp_scope':dhcp_scope
           },
           RequestContext(request))
def showfile(request, dhcp_scope):
    #scope = get_object_or_404(models.DHCP, pk=id)
    #truth = Truth.objects.get(name='phx-vlan73')
    #scope = TruthKeyValue(truth=truth)
    client = Client()
    resp = client.get('/api/keyvalue/?keystore=%s' % dhcp_scope)
    scope=json.loads(resp.content)
    scope_options = {}
    if 'dhcp.scope.start' in scope:
        scope_options['network_block'] = scope['dhcp.scope.start']
    if 'dhcp.scope.netmask' in scope:
        scope_options['subnet_mask'] = scope['dhcp.scope.netmask']
    if 'dhcp.pool.start' in scope:
        scope_options['pool_range_start'] = scope['dhcp.pool.start']
    if 'dhcp.pool.end' in scope:
        scope_options['pool_range_end'] = scope['dhcp.pool.end']
    if 'dhcp.pool.allow_booting.0' in scope and scope['dhcp.pool.allow_booting.0'] is not None:
        scope_options['allow_booting'] = 1
    if 'dhcp.pool.allow_bootp.0' in scope and scope['dhcp.pool.allow_bootp.0'] is not None:
        scope_options['allow_bootp'] = 1

    if 'dhcp.option.domain_name.0' in scope and scope['dhcp.option.domain_name.0'] is not None:
        scope_options['option_domain_name'] = scope['dhcp.option.domain_name.0']
    if 'dhcp.option.domain_name.1' in scope and scope['dhcp.option.domain_name.1'] is not None:
        scope_options['option_domain_name'] += ', ' + scope['dhcp.option.domain_name.1']
    if 'dhcp.option.domain_name.2' in scope and scope['dhcp.option.domain_name.2'] is not None:
        scope_options['option_domain_name'] += ', ' + scope['dhcp.option.domain_name.2']

    if 'dhcp.option.ntp_server.0' in scope and scope['dhcp.option.ntp_server.0'] is not None:
        scope_options['option_ntp_servers'] = scope['dhcp.option.ntp_server.0']
    if 'dhcp.option.ntp_server.1' in scope and scope['dhcp.option.ntp_server.1'] is not None:
        scope_options['option_ntp_servers'] += ', ' + scope['dhcp.option.ntp_server.1']
    if 'dhcp.option.ntp_server.2' in scope and scope['dhcp.option.ntp_server.2'] is not None:
        scope_options['option_ntp_servers'] += ', ' + scope['dhcp.option.ntp_server.2']

    if 'dhcp.option.router.0' in scope and scope['dhcp.option.router.0'] is not None:
        scope_options['option_routers'] = scope['dhcp.option.router.0']

    if 'dhcp.option.subnet_mask.0' in scope and scope['dhcp.option.subnet_mask.0'] is not None:
        scope_options['option_subnet_mask'] = scope['dhcp.option.subnet_mask.0']
    scope_options['notes'] = '' #scope.scope_notes
    try:
        scope_options['overrides'] = models.DHCPOverride.objects.get(dhcp_scope=dhcp_scope).override_text #scope.scope_notes
        if scope_options['overrides'] is None:
            scope_options['overrides'] = ''
    except:
        d = models.DHCPOverride(dhcp_scope=dhcp_scope)
        d.save()
        scope_options['overrides'] = models.DHCPOverride.objects.get(dhcp_scope=dhcp_scope) #scope.scope_notes
        if scope_options['overrides'] is None:
            scope_options['overrides'] = ''
    """scope_options['allow_booting'] = scope.allow_booting
    scope_options['allow_bootp'] = scope.allow_bootp
    scope_options['filename'] = scope.filename
    scope_options['pool_deny_dynamic_bootp_agents'] = scope.pool_deny_dynamic_bootp_agents
    scope_options['option_ntp_servers'] = scope.option_ntp_servers
    scope_options['option_subnet_mask'] = scope.option_subnet_mask
    scope_options['option_domain_name'] = scope.option_domain_name
    scope_options['option_domain_name_servers'] = scope.option_domain_name_servers
    scope_options['option_routers'] = scope.option_routers"""
    

    #hostsAll = NetworkAdapter.objects.filter(dhcp_scope = id)
    hosts = json.loads(client.get('/api/keyvalue/?key_type=system_by_scope&scope=%s' % dhcp_scope).content)
    #print hosts
    adapter_list = []
    for host in hosts:
        the_url = '/api/keyvalue/?key_type=adapters_by_system_and_scope&dhcp_scope=%s&system=%s' % (dhcp_scope, host['hostname'])
        adapter_list.append(json.loads(client.get(the_url).content))

    #print adapter_list

    d = DHCP(scope_options, adapter_list)
    output = d.notes()
    #output += d.header()
    #output += d.pool()
    #output += d.options()
    output += d.get_hosts()
    #output += d.footer()
    output = output.replace("\n","<br />")
    return render_to_response('dhcp/showfile.html', {

        "output": output 
        },
        RequestContext(request))
def create(request):
    if request.method == 'POST':
        form = forms.AddDHCPScopeForm(request.POST)
        if form.is_valid():
            pass
            #s = form.save()
            #return redirect('/dhcp/show/')
    else:
        form = forms.AddDHCPScopeForm()

    return render_to_response('dhcp/new.html', {
            "form": form 
           },
           RequestContext(request))
def edit(request, dhcp_scope):
    client = Client()
    resp = client.get('/api/keyvalue/?keystore=%s' % dhcp_scope)
    instance = json.loads(resp.content)
    initial = {}
    initial['scope_name'] = dhcp_scope
    ##A bunch of try/catch blocks to create key/value pairs if one does not exist
    try:
        initial['scope_start'] = instance['dhcp.scope.start']
    except:
        client.post('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.scope.start', 'value':'', 'truth_name':dhcp_scope})
        initial['scope_start'] = ''
    try:
        initial['scope_end'] = instance['dhcp.scope.end']
    except:
        client.post('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.scope.end', 'value':'', 'truth_name':dhcp_scope})
        initial['scope_end'] = ''
    try:
        initial['scope_netmask'] = instance['dhcp.scope.netmask']
    except:
        client.post('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.scope.netmask', 'value':'', 'truth_name':dhcp_scope})
        initial['scope_netmask'] = ''
    try:
        initial['pool_start'] = instance['dhcp.pool.start']
    except:
        client.post('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.pool.start', 'value':'', 'truth_name':dhcp_scope})
        initial['pool_start'] = ''
    try:
        initial['pool_end'] = instance['dhcp.pool.end']
    except:
        client.post('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.pool.end', 'value':'', 'truth_name':dhcp_scope})
        initial['pool_end'] = ''
    try:
        initial['ntp_server1'] = instance['dhcp.option.ntp_server.0']
    except:
        client.post('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.option.ntp_server.0', 'value':'', 'truth_name':dhcp_scope})
        initial['ntp_server1'] = ''
    try:
        initial['ntp_server2'] = instance['dhcp.option.ntp_server.0']
    except:
        client.post('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.option.ntp_server.1', 'value':'', 'truth_name':dhcp_scope})
        initial['ntp_server2'] = ''
    try:
        initial['router'] = instance['dhcp.option.router.0']
    except:
        client.post('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.option.router.0', 'value':'', 'truth_name':dhcp_scope})
        initial['router'] = ''
    try:
        initial['domain_name'] = instance['dhcp.option.domain_name.0']
    except:
        client.post('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.option.domain_name.0', 'value':'', 'truth_name':dhcp_scope})
        initial['domain_name'] = ''
    try:
        initial['dns_server1'] = instance['dhcp.dns_server.0']
    except:
        client.post('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.dns_server.0', 'value':'', 'truth_name':dhcp_scope})
        initial['dns_server1'] = ''
    try:
        initial['dns_server2'] = instance['dhcp.dns_server.0']
    except:
        client.post('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.dns_server.1', 'value':'', 'truth_name':dhcp_scope})
        initial['dns_server2'] = ''
    try:
        initial['allow_booting'] = instance['dhcp.pool.allow_booting.0']
    except:
        client.post('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.pool.allow_booting.0', 'value':'', 'truth_name':dhcp_scope})
        initial['allow_booting'] = ''
    try:
        initial['allow_bootp'] = instance['dhcp.pool.allow_bootp.0']
    except:
        client.post('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.pool.allow_bootp.0', 'value':'', 'truth_name':dhcp_scope})
        initial['allow_bootp'] = ''

    if request.method == 'POST':
        form = forms.EditDHCPScopeForm(request.POST)
        if form.is_valid():
            client.put('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.scope.start', 'value':form.cleaned_data['scope_start']})
            client.put('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.scope.end', 'value':form.cleaned_data['scope_end']})
            client.put('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.scope.netmask', 'value':form.cleaned_data['scope_netmask']})
            client.put('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.pool.start', 'value':form.cleaned_data['pool_start']})
            client.put('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.pool.end', 'value':form.cleaned_data['pool_end']})
            client.put('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.option.ntp_server.0', 'value':form.cleaned_data['ntp_server1']})
            client.put('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.option.ntp_server.1', 'value':form.cleaned_data['ntp_server2']})
            client.put('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.dns_server.0', 'value':form.cleaned_data['dns_server1']})
            client.put('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.dns_server.1', 'value':form.cleaned_data['dns_server2']})
            client.put('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.option.domain_name.0', 'value':form.cleaned_data['domain_name']})
            client.put('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.option.router.0', 'value':form.cleaned_data['router']})
            client.put('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.pool.allow_booting.0', 'value':form.cleaned_data['allow_booting']})
            client.put('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.pool.allow_bootp.0', 'value':form.cleaned_data['allow_bootp']})
    else:
        form = forms.EditDHCPScopeForm(initial=initial)

    return render_to_response('dhcp/edit.html', {
            "form": form,
            'dhcp_scope': dhcp_scope
           },
           RequestContext(request))
def delete(request, dhcp_scope):
    try:
        scope = Truth.objects.get(name=dhcp_scope)
        TruthKeyValue.objects.filter(truth=scope).delete()
        scope.delete()
        return redirect('/dhcp/show/')
    except:    
        return redirect('/dhcp/show/')
