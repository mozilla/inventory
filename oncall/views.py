from django.shortcuts import render
from django.http import HttpResponse

from oncall.models import OncallAssignment
from oncall.forms import OncallForm
from oncall.constants import ONCALL_TYPES

import simplejson as json


def getoncall(request, oncall_type):
    """
    Returns information about who is oncall. Oncall types include 'desktop',
    'sysadmin', and 'services'.

    Use ?format=<format> to determine the format of the response.

    Format 'json':
        {
            "irc_nic": <IRC nick>,
            "ldap_username": <Username>,
            "pager_type": <Pager type>,
            "pager_number": <Pager number>,
            "epager_address": <Epager address>
        }

    Format 'delimited':
        <IRC nick>:<Username>:<Pager type>:<Pager number>:<Epager address>

    Format 'meta':
        The field names returned by 'delimited'

    You can use the 'meta' format like you would use the first line of a CSV to
    determine what fields are being returned by 'delimited'.
    """

    if oncall_type not in ONCALL_TYPES:
        return HttpResponse('nobody')

    profile = OncallAssignment.objects.get(
        oncall_type=oncall_type
    ).user.get_profile()

    format = request.GET.get('format', 'basic')

    if format == 'basic':
        response = profile.irc_nick
    elif format in ('json', 'delimited', 'meta'):
        attrs = (
            ("irc_nic", profile.irc_nick or ''),
            ("ldap_username", profile.user.username or ''),
            ("pager_type", profile.pager_type or ''),
            ("pager_number", profile.pager_number or ''),
            ("epager_address", profile.epager_address or '')
        )
        if format == 'json':
            response = json.dumps(dict(attrs))
        elif format == 'delimited':
            response = ':'.join([el[1] for el in attrs])
        elif format == 'meta':
            response = ':'.join([el[0] for el in attrs])

    return HttpResponse(response)


def oncall(request):
    if request.method == 'POST':
        form = OncallForm(request.POST)
        if form.is_valid():
            form.save()
        else:
            return render(
                request,
                'systems/generic_form.html',
                {'form': form}
            )

    initial = {}
    for onct in ONCALL_TYPES:
        try:
            cur = OncallAssignment.objects.get(oncall_type=onct)
            cur_onc_name = cur.user.username
        except OncallAssignment.DoesNotExist:
            cur_onc_name = ''
    initial[onct] = cur_onc_name
    form = OncallForm(initial=initial)
    return render(
        request,
        'systems/generic_form.html',
        {'form': form}
    )
