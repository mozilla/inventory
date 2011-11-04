# Create your views here.
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, InvalidPage, EmptyPage

from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import simplejson as json
import models
import forms


import re
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

def create(request):
    if request.POST:
        f = forms.TruthForm(request.POST)
        if f.is_valid():
            f.save()
            return HttpResponseRedirect('/truth/')
    else:
        f = forms.TruthForm()
    return render_to_response('truth/key_value_store_create.html', {
            'form': f,
           },
           RequestContext(request))


def delete(request, id):
    t = models.Truth.objects.get(id=id) 
    models.KeyValue.objects.filter(truth=t).delete()
    t.delete()
    return HttpResponseRedirect('/truth/')

def edit(request, id):
    truth = models.Truth.objects.get(id=id) 
    if request.POST:
        f = forms.TruthForm(request.POST, instance=truth)
        if f.is_valid():
            f.save()
    else:
        f = forms.TruthForm(instance=truth)
    return render_to_response('truth/edit.html', {
            'kv': truth,
            'form': f
        },RequestContext(request))
def index(request):
    
    return render_to_response('truth/index.html', {
            'systems': models.Truth.objects.all(),
            'read_only': getattr(request, 'read_only', False),
        },RequestContext(request))
        
def get_key_value_store(request, id):
    truth = models.Truth.objects.get(id=id)
    key_value_store = models.KeyValue.objects.filter(truth=truth)
    return render_to_response('truth/key_value_store.html', {
            'key_value_store': key_value_store,
           },
           RequestContext(request))
def delete_key_value(request, id, kv_id):
    kv = models.KeyValue.objects.get(id=id)
    kv.delete()
    truth = models.Truth.objects.get(id=kv_id)
    key_value_store = models.KeyValue.objects.filter(truth=truth)
    return render_to_response('truth/key_value_store.html', {
            'key_value_store': key_value_store,
           },
           RequestContext(request))
def save_key_value(request, id):
    kv = models.KeyValue.objects.get(id=id)
    if kv is not None:
        kv.key = request.POST['key']
        kv.value = request.POST['value']
        truth_id = str(kv.truth_id)
        kv.save()
    return HttpResponseRedirect('/truth/get_key_value_store/' + truth_id + '/')

def create_key_value(request, id):
    truth = models.Truth.objects.get(id=id)
    kv = models.KeyValue(truth=truth)
    kv.save();
    key_value_store = models.KeyValue.objects.filter(truth=truth)
    return render_to_response('truth/key_value_store.html', {
            'key_value_store': key_value_store,
           },
           RequestContext(request))

def list_all_keys_ajax(request):
#iSortCol_0 = which column is sorted
#sSortDir_0 = which direction 	
    
    cols = ['name','description']
    sort_col = cols[0]
    if 'iSortCol_0' in request.GET:
        sort_col = cols[int(request.GET['iSortCol_0'])]

    sort_dir = 'asc'
    if 'sSortDir_0' in request.GET:
        sort_dir = request.GET['sSortDir_0']


    if 'sEcho' in request.GET:
        sEcho = request.GET['sEcho']
    else:
        sEcho = 0

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
        system_count = models.Truth.objects.all().count()
        systems = models.Truth.objects.all()[iDisplayStart:end_display]
        the_data = build_json(request, systems, sEcho, system_count, iDisplayLength, sort_col, sort_dir)

    if search_term is not None and len(search_term) > 0:
				
        search_q = Q(name__contains=search_term)
        search_q |= Q(description__contains=search_term)
        total_count = models.Truth.objects.filter(search_q).count()
        end_display = int(iDisplayStart) + int(iDisplayLength)
        systems = models.Truth.objects.filter(search_q).order_by('name')[iDisplayStart:end_display]
        the_data = build_json(request, systems, sEcho, total_count, iDisplayLength, sort_col, sort_dir)
    return HttpResponse(the_data)

def build_json(request, systems, sEcho, total_records, display_count, sort_col, sort_dir):
    system_list = []
    for system in systems:

        system_list.append({'name': system.name.strip(), 'description': system.description, 'id':system.id})

    the_data = '{"sEcho": %s, "iTotalRecords":0, "iTotalDisplayRecords":0, "aaData":[]}' % (sEcho)

    #try:
    if len(system_list) > 0:
        system_list.sort(key=lambda x: alphanum_key(x[sort_col]))
        if sort_dir == 'desc':
            system_list.reverse()


        the_data = '{"sEcho": %s, "iTotalRecords":%i, "iTotalDisplayRecords":%i, "aaData":[' % (sEcho,  total_records, total_records)
        counter = 0
        for system in system_list:
            if counter < display_count:
                the_data += '["%s","%s","%s"],' % (system['name'],system['description'],system['id'])
                counter += 1
            else:
                counter = display_count
        the_data = the_data[:-1]
        the_data += ']}'
    #except:
        pass
    
    return the_data 
