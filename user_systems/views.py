import csv
import operator

from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.forms.extras.widgets import SelectDateWidget
from django.db import connection
from django.db.models import Q
from django.utils import simplejson as json
from django.http import HttpResponse
from django.core.mail import send_mail

import forms
import models
from systems import models as system_models
from libs import ldap_lib
from settings.local import USER_SYSTEM_ALLOWED_DELETE
from django.shortcuts import render_to_response, redirect, get_object_or_404
def license_quicksearch_ajax(request):
    """Returns systems sort table"""
    search = request.POST['quicksearch']
    filters = [Q(**{"%s__icontains" % t: search})
                    for t in models.UserLicense.search_fields]

    licenses = models.UserLicense.objects.filter(
                reduce(operator.or_, filters))

    return render_to_response('user_systems/license_quicksearch.html', {
            'licenses': licenses,
           },
           RequestContext(request))
def user_system_quicksearch_ajax(request):
    """Returns systems sort table"""
    search = request.POST['quicksearch']
    filters = [Q(**{"%s__icontains" % t: search})
                    for t in models.UnmanagedSystem.search_fields]

    systems = models.UnmanagedSystem.objects.filter(
                reduce(operator.or_, filters))

    return render_to_response('user_systems/quicksearch.html', {
            'systems': systems,
           },
           RequestContext(request))


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
                        system=saved_instance).save()
                if saved_instance.notes:
                    models.History(
                        change="Notes changed to %s" % saved_instance.notes,
                        system=saved_instance).save()
                else:
                    models.History(
                        change="System has no Notes",
                        system=saved_instance).save()
            if not instance or old_asset_tag != saved_instance.asset_tag:
                if old_asset_tag:
                    models.History(
                        change="Asset Tag changed from %s" % old_asset_tag,
                        system=saved_instance).save()
                if saved_instance.asset_tag:
                    models.History(
                        change="Asset Tag changed to %s" % saved_instance.asset_tag,
                        system=saved_instance).save()
                else:
                    models.History(
                        change="System has no Asset Tag",
                        system=saved_instance).save()
            if not instance or old_serial != saved_instance.serial:
                if old_serial:
                    models.History(
                        change="Serial changed from %s" % old_serial,
                        system=saved_instance).save()
                if saved_instance.serial:
                    models.History(
                        change="Serial changed to %s" % saved_instance.serial,
                        system=saved_instance).save()
                else:
                    models.History(
                        change="System has no serial",
                        system=saved_instance).save()
            if not instance or old_owner != saved_instance.owner:
                if old_owner:
                    models.History(
                        change="Owner changed from %s" % old_owner,
                        system=saved_instance).save()
                if saved_instance.owner:
                    models.History(
                        change="Owner changed to %s" % saved_instance.owner,
                        system=saved_instance).save()
                else:
                    models.History(
                        change="System has no owner",
                        system=saved_instance).save()
            return redirect('user-system-list')
    else:
        form = forms.UserSystemForm(instance=instance)

    data['form'] = form
    the_owner_list = ldap_lib.get_all_names()
    the_owner_list.append("STOCK")
    the_owner_list.append("STOCK-SFO")
    the_owner_list.append("STOCK-MTV")
    the_owner_list.append("STOCK-TOR")
    data['owner_json'] = json.dumps(the_owner_list)
    #data['owner_json'] = json.dumps(ldap_lib.get_all_names())
    #data['owner_json'].append("Stock")

    return render_to_response(template, data, RequestContext(request))

def license_delete(request, object_id):
    from misc.generic_views import delete_object
    license = get_object_or_404(models.UserLicense, pk=object_id)
    if request.user.username in USER_SYSTEM_ALLOWED_DELETE:
        return delete_object(request, model=models.UserLicense, object_id=object_id,post_delete_redirect='license-list')
    else:
        send_mail('Unauthorized Delete Attempt', 'Unauthorized Attempt to Delete %s by %s' % (license, request.user.username), settings.local.FROM_EMAIL_ADDRESS,settings.local.UNAUTHORIZED_EMAIL_ADDRESS, fail_silently=False)
                    
        return render_to_response('user_systems/unauthorized_delete.html', {
                'content': "You're not authorized to delete",
            },
            RequestContext(request))
def unmanaged_system_delete(request, object_id):
    from misc.generic_views import delete_object
    user_system = get_object_or_404(models.UnmanagedSystem, pk=object_id)
    if request.user.username in USER_SYSTEM_ALLOWED_DELETE:
        return delete_object(request, model=models.UnmanagedSystem, object_id=object_id,post_delete_redirect='user-system-list')
    else:
        send_mail('Unauthorized Delete Attempt', 'Unauthorized Attempt to Delete %s by %s' % (user_system, request.user.username), settings.local.FROM_EMAIL_ADDRESS,settings.local.UNAUTHORIZED_EMAIL_ADDRESS, fail_silently=False)
                    
        return render_to_response('user_systems/unauthorized_delete.html', {
                'content': "You're not authorized to delete",
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


def user_system_edit(request, id):
    system = get_object_or_404(models.UnmanagedSystem, pk=id)

    return user_system_view(
        request,
        'user_systems/unmanagedsystem_modify.html', {
            'system': system},
        system)


def user_system_csv(request):
    systems = models.UnmanagedSystem.objects.all().order_by('owner__name')

    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=user_systems.csv'

    writer = csv.writer(response)
    writer.writerow(['Owner', 'Location', 'Serial', 'Asset Tag',
                    'Operating System', 'Model', 'Date Purchased', 'Cost'])

    for s in systems:
        location = s.owner.user_location
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
