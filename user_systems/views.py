import csv
import operator

from django.template import RequestContext
from django.forms.extras.widgets import SelectDateWidget
from django.db import connection
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils import simplejson as json
from django.http import HttpResponse, HttpResponseRedirect
from django.core.mail import send_mail

import forms
import models
from systems import models as system_models
from datetime import datetime, timedelta
from libs import ldap_lib
import settings
from settings.local import USER_SYSTEM_ALLOWED_DELETE, FROM_EMAIL_ADDRESS, UNAUTHORIZED_EMAIL_ADDRESS
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, get_object_or_404, render
from libs.jinja import render_to_response as render_to_response
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from MozInvAuthorization.UnmanagedSystemACL import UnmanagedSystemACL

def license_version_search(request):
    query = request.GET.get('query')
    tmp = [str(m['version']) for m in models.UserLicense.objects.filter(version__icontains=query).values('version').distinct()]
    versions = list(set(tmp))
    ret_dict = {}
    ret_dict['query'] = query
    ret_dict['suggestions'] = versions
    ret_dict['data'] = versions
    return HttpResponse(json.dumps(ret_dict))

def license_type_search(request):
    query = request.GET.get('query')
    types = [m['license_type'] for m in models.UserLicense.objects.filter(license_type__icontains=query).values('license_type').distinct()]
    ret_dict = {}
    ret_dict['query'] = query
    ret_dict['suggestions'] = types
    ret_dict['data'] = types
    return HttpResponse(json.dumps(ret_dict))
@csrf_exempt
def owners_quicksearch_ajax(request):
    """Returns systems sort table"""
    search = request.POST['quicksearch']
    filters = [Q(**{"%s__icontains" % t: search})
                    for t in models.Owner.search_fields]

    owners = models.Owner.objects.filter(
                reduce(operator.or_, filters))

    return render_to_response('user_systems/owners_quicksearch.html', {
            'owners': owners,
           },
           RequestContext(request))
@csrf_exempt
def license_edit(request, object_id):
    license = get_object_or_404(models.UserLicense, pk=object_id)
    if request.method == 'POST':
        form = forms.UserLicenseForm(request.POST, instance=license)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/user_systems/licenses/')
    else:
        form = forms.UserLicenseForm(instance=license)

    return render_to_response('user_systems/userlicense_form.html', {
            'form': form,
           },
           RequestContext(request))
def owner_list(request):
    owners = models.Owner.objects.select_related('user_location').all()
    upgradeable_users = models.Owner.objects.filter(unmanagedsystem__date_purchased__lt=datetime.now() - timedelta(days=730)).distinct().count()
    return render_to_response('user_systems/owner_list.html', {
            'owner_list': owners,
            'upgradeable_users':upgradeable_users,
           },
           RequestContext(request))
def owner_show(request, object_id):
    owner = get_object_or_404(models.Owner, pk=object_id)

    return render_to_response('user_systems/owner_detail.html', {
            'owner': owner,
           },
           RequestContext(request))

def owner_delete(request, object_id):
    owner = get_object_or_404(models.Owner, pk=object_id)
    if request.method == "POST":
        owner.delete()
        return HttpResponseRedirect('/user_systems/owners/')
    else:
        return render_to_response('user_systems/owner_confirm_delete.html', {
                'owner': owner,
            },
            RequestContext(request))
@csrf_exempt
def owner_edit(request, object_id):
    owner = get_object_or_404(models.Owner, pk=object_id)
    initial = {}
    if request.method == 'POST':
        form = forms.OwnerForm(request.POST, instance=owner)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/user_systems/owners/')
    else:
        form = forms.OwnerForm(instance=owner)

    return render_to_response('user_systems/owner_form.html', {
            'form': form,
           },
           RequestContext(request))
def owner_create(request):
    initial = {}
    if request.method == 'POST':
        form = forms.OwnerForm(request.POST, initial=initial)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/user_systems/owners/')
    else:
        form = forms.OwnerForm(initial=initial)

    return render_to_response('user_systems/owner_form.html', {
            'form': form,
           },
           RequestContext(request))

def license_new(request):
    initial = {}
    if request.method == 'POST':
        form = forms.UserLicenseForm(request.POST, initial=initial)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/user_systems/licenses/')
    else:
        form = forms.UserLicenseForm(initial=initial)

    return render_to_response('user_systems/userlicense_form.html', {
            'form': form,
           },
           RequestContext(request))

def license_quicksearch_ajax(request):
    """Returns systems sort table"""
    # Try to get quicksearch from post
    # If fail, try to get from GET
    # return None otherwise
    search = request.GET.get('quicksearch', None)
    if search:
        filters = [Q(**{"%s__icontains" % t: search})
                        for t in models.UserLicense.search_fields]

        licenses = models.UserLicense.objects.filter(
                    reduce(operator.or_, filters))
    else:
        licenses = None
    return render_to_response('user_systems/license_quicksearch.html', {
            'licenses': licenses,
           },
           RequestContext(request))

@csrf_exempt
def user_system_quicksearch_ajax(request):
    """Returns systems sort table"""
    from settings import BUG_URL as BUG_URL
    search = request.POST['quicksearch']
    print request.POST
    filters = [Q(**{"%s__icontains" % t: search})
                    for t in models.UnmanagedSystem.search_fields]

    systems = models.UnmanagedSystem.objects.filter(
                reduce(operator.or_, filters))

    return render_to_response('user_systems/quicksearch.html', {
            'systems': systems,
            'BUG_URL': BUG_URL,
           },
           RequestContext(request))

@csrf_exempt
def user_system_view(request, template, data, instance=None):
    if request.method == 'POST':
        post_data = request.POST.copy()

        owner, c = models.Owner.objects.get_or_create(
            name=request.POST['owner_name'])

        post_data['owner'] = owner.id

        try:
            os, c = models.OperatingSystem.objects.get_or_create(
                    name=request.POST['js_os_name'],
                    version=request.POST['js_os_version'])
            post_data['operating_system'] = os.id
        except KeyError:
            pass

        try:
            server_model, c = models.ServerModel.objects.get_or_create(
                            vendor=request.POST['js_server_model_vendor'],
                            model=request.POST['js_server_model_model'])
            post_data['server_model'] = server_model.id
        except KeyError:
            pass

        if instance:
            old_owner = instance.owner
            old_serial = instance.serial
            old_asset_tag = instance.asset_tag
            old_notes = instance.notes
        else:
            old_owner = None
            old_serial = None
            old_asset_tag = None
            old_notes = None

        form = forms.UserSystemForm(post_data, instance=instance)
        if form.is_valid():
            saved_instance = form.save()
            if not instance or old_notes != saved_instance.notes:
                if old_notes:
                    models.History(
                        change="Notes changed from %s" % old_notes,
                        changed_by=get_changed_by(request),
                        system=saved_instance).save()
                if saved_instance.notes:
                    models.History(
                        change="Notes changed to %s" % saved_instance.notes,
                        changed_by=get_changed_by(request),
                        system=saved_instance).save()
                else:
                    models.History(
                        change="System has no Notes",
                        changed_by=get_changed_by(request),
                        system=saved_instance).save()
            if not instance or old_asset_tag != saved_instance.asset_tag:
                if old_asset_tag:
                    models.History(
                        change="Asset Tag changed from %s" % old_asset_tag,
                        changed_by=get_changed_by(request),
                        system=saved_instance).save()
                if saved_instance.asset_tag:
                    models.History(
                        change="Asset Tag changed to %s" % saved_instance.asset_tag,
                        changed_by=get_changed_by(request),
                        system=saved_instance).save()
                else:
                    models.History(
                        change="System has no Asset Tag",
                        changed_by=get_changed_by(request),
                        system=saved_instance).save()
            if not instance or old_serial != saved_instance.serial:
                if old_serial:
                    models.History(
                        change="Serial changed from %s" % old_serial,
                        changed_by=get_changed_by(request),
                        system=saved_instance).save()
                if saved_instance.serial:
                    models.History(
                        change="Serial changed to %s" % saved_instance.serial,
                        changed_by=get_changed_by(request),
                        system=saved_instance).save()
                else:
                    models.History(
                        change="System has no serial",
                        changed_by=get_changed_by(request),
                        system=saved_instance).save()
            if not instance or old_owner != saved_instance.owner:
                if old_owner:
                    models.History(
                        change="Owner changed from %s" % old_owner,
                        changed_by=get_changed_by(request),
                        system=saved_instance).save()
                if saved_instance.owner:
                    models.History(
                        change="Owner changed to %s" % saved_instance.owner,
                        changed_by=get_changed_by(request),
                        system=saved_instance).save()
                else:
                    models.History(
                        change="System has no owner",
                        changed_by=get_changed_by(request),
                        system=saved_instance).save()
            return redirect('user-system-list')
    else:
        form = forms.UserSystemForm(instance=instance)

    data['form'] = form
    if settings.USE_LDAP:
        the_owner_list = ldap_lib.get_all_names()
    else:
        the_owner_list = []
    the_owner_list.append("STOCK")
    the_owner_list.append("STOCK-SFO")
    the_owner_list.append("STOCK-MTV")
    the_owner_list.append("STOCK-TOR")
    the_owner_list.append("STOCK-LON")
    the_owner_list.append("STOCK-LON")
    the_owner_list.append("desktop-mtv1")
    the_owner_list.append("desktop-sfo1")
    the_owner_list.append("desktop-tor1")
    the_owner_list.append("desktop-lon1")
    the_owner_list.append("desktop-par1")
    the_owner_list.append("desktop-yvr1")
    data['owner_json'] = json.dumps(the_owner_list)

    #data['owner_json'] = json.dumps(ldap_lib.get_all_names())
    #data['owner_json'].append("Stock")

    return render_to_response(template, data, RequestContext(request))
def get_changed_by(request):
    try:
        remote_user = request.META['REMOTE_USER']
    except:
        remote_user = None

    return remote_user

#def license_new(request):
#	return render_to_response('user_systems/userlicense_new.html')

def license_show(request, object_id):
    license = get_object_or_404(models.UserLicense, pk=object_id)

    return render_to_response('user_systems/userlicense_detail.html', {
            'license': license,
            },RequestContext(request) )
def license_index(request):
    from settings import BUG_URL as BUG_URL
    system_list = models.UserLicense.objects.select_related('owner').all()
    paginator = Paginator(system_list, 25)                                                                        
                    
    if 'page' in request.GET:
        page = request.GET.get('page')
    else:   
        page = 1
        
    try:
        systems = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        systems = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        systems = paginator.page(paginator.num_pages)

    return render_to_response('user_systems/userlicense_list.html', {
            'license_list': systems,
            'BUG_URL': BUG_URL
            },RequestContext(request) )
def user_system_index(request):
    from settings import BUG_URL as BUG_URL
    system_list = models.UnmanagedSystem.objects.select_related('owner', 'server_model', 'operating_system').order_by('owner__name')
    paginator = Paginator(system_list, 25)                                                                        
                    
    if 'page' in request.GET:
        page = request.GET.get('page')
    else:   
        page = 1
        
    try:
        systems = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        systems = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        systems = paginator.page(paginator.num_pages)

    return render_to_response('user_systems/unmanagedsystem_list.html', {
            'user_system_list': systems,
            'BUG_URL': BUG_URL
            },RequestContext(request) )
        

def license_delete(request, object_id):
    license = get_object_or_404(models.UserLicense, pk=object_id)
    try:
        license.delete()
        return HttpResponseRedirect( reverse('license-list') )
    except PermissionDenied, e:
        return render_to_response('user_systems/unauthorized_delete.html', {
                'content': 'You do not have permission to delete this license',
            },
            RequestContext(request))

def unmanaged_system_delete(request, object_id):
    #Dummy comment
    user_system = get_object_or_404(models.UnmanagedSystem, pk=object_id)
    if request.method == 'POST':
        try:
            acl = UnmanagedSystemACL(request)
            acl.check_delete()
            user_system_notes = user_system.notes
            user_system.delete()
            send_mail('System Deleted', '%s Deleted by %s\nSystem Notes:\n%s' % (user_system, request.user.username, user_system_notes), FROM_EMAIL_ADDRESS, UNAUTHORIZED_EMAIL_ADDRESS, fail_silently=False)
            return HttpResponseRedirect( reverse('user-system-list') )
        except PermissionDenied, e:
            send_mail('Unauthorized System Delete Attempt', 'Unauthorized Attempt to Delete %s by %s' % (user_system, request.user.username), FROM_EMAIL_ADDRESS, UNAUTHORIZED_EMAIL_ADDRESS, fail_silently=False)
            return render_to_response('user_systems/unauthorized_delete.html', {
                    'content': 'You do not have permission to delete this system',
                },
                RequestContext(request))
    else:
        return render_to_response('user_systems/unmanagedsystem_confirm_delete.html', {
                'owner': user_system,
            },
            RequestContext(request))
                    

def show_by_model(request, object_id):
    system_list = models.UnmanagedSystem.objects.filter(server_model=models.ServerModel.objects.get(id=object_id))
    if 'show_all' in request.GET:
        paginator = Paginator(system_list, system_list.count())                                                                        
    else:
        paginator = Paginator(system_list, 25)                                                                        
                    
    if 'page' in request.GET:
        page = request.GET.get('page')
    else:   
        page = 1
        
    try:
        systems = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        systems = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        systems = paginator.page(paginator.num_pages)
    return render_to_response('user_systems/unmanagedsystem_list.html', {
            'user_system_list': systems,
            'show_all': True,
           },
           RequestContext(request))

def user_system_show(request, object_id):
    system = get_object_or_404(models.UnmanagedSystem, id=object_id)
    #system = models.UnmanagedSystem.objects.select_related(
    #                'owner', 'server_model', 'operating_system'
    #                 ).filter(asset_tag=id).order_by('owner__name')

    #system = get_object_or_404(models.UnmanagedSystem
    return render_to_response('user_systems/unmanagedsystem_detail.html', {
            'user_system': system,
            'settings': settings,
           },
           RequestContext(request))
def user_system_show_by_asset_tag(request, id):
    system = get_object_or_404(models.UnmanagedSystem, asset_tag=id)
    #system = models.UnmanagedSystem.objects.select_related(
    #                'owner', 'server_model', 'operating_system'
    #                 ).filter(asset_tag=id).order_by('owner__name')

    #system = get_object_or_404(models.UnmanagedSystem
    return render_to_response('user_systems/unmanagedsystem_detail.html', {
            'user_system': system,
           },
           RequestContext(request))


def user_system_new(request):
    return user_system_view(
        request,
        'user_systems/unmanagedsystem_create.html',
        {})


@csrf_exempt
def user_system_edit(request, id):
    system = get_object_or_404(models.UnmanagedSystem, pk=id)

    return user_system_view(
        request,
        'user_systems/unmanagedsystem_modify.html', {
            'system': system},
        system)


def user_system_csv(request):
    systems = models.UnmanagedSystem.objects.all().order_by('owner__name')
    try:
        ref_split = request.META['HTTP_REFERER'].split('/')
        type, id = ref_split[-3:-1]
        if type == 'model':
            systems = systems.filter(server_model__id=id)
    except:
        pass


    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=user_systems.csv'

    writer = csv.writer(response)
    writer.writerow(['Owner', 'Location', 'Serial', 'Asset Tag',
                    'Operating System', 'Model', 'Date Purchased', 'Cost'])

    for s in systems:
        try:
            location = s.owner.user_location
        except AttributeError:
            location = ''
        writer.writerow([s.owner, location, s.serial, s.asset_tag,
                s.operating_system, s.server_model, s.date_purchased, s.cost])

    return response


def fillin_csv(request):
    """Important columns:
            4: serial number
            6: employee
            7: location
    """

    if request.method == 'POST':
        f = forms.CSVForm(request.POST, request.FILES)
        if f.is_valid():
            response = HttpResponse(mimetype='text/csv')
            response['Content-Disposition'] = 'attachment; filename=ComputerEquipment.csv'
            in_csv = csv.reader(f.cleaned_data['csv'].read().splitlines())
            out_csv = csv.writer(response)
            for row in in_csv:
                if row[4]:
                    serials = [i.strip() for i in row[4].split(';')]
                    owners = [
                        str(i.owner)
                        for i in models.UnmanagedSystem.objects.filter(
                            serial__in=serials).filter(owner__isnull=False)]
                    locations = [
                        str(i.system_rack.location)
                        for i in system_models.System.objects.filter(
                            serial__in=serials).filter(system_rack__location__isnull=False)]

                    locations += [
                        str(i.owner.user_location)
                        for i in models.UnmanagedSystem.objects.filter(
                            serial__in=serials).filter(owner__user_location__isnull=False)]

                    if owners:
                        row[6] = "; ".join(owners)
                    if locations:
                        row[7] = "; ".join(locations)

                out_csv.writerow(row)
            return response
    else:
        f = forms.CSVForm()

    return render_to_response(
        'user_systems/fillin_csv.html',
        {'form': f},
        RequestContext(request))
