from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.http import HttpResponse

from core.utils import int_to_ip, resolve_ip_type
from core.range.forms import RangeForm
from core.range.utils import range_usage
from core.range.ip_choosing_utils import (
    calculate_filters, label_value_maker, calc_template_ranges,
    integrate_real_ranges, UN
)
from core.range.models import Range
from core.site.models import Site
from core.vlan.models import Vlan
from core.network.models import Network
from mozdns.ip.models import ipv6_to_longs
from core.views import CoreDeleteView, CoreDetailView
from core.views import CoreCreateView, CoreUpdateView, CoreListView

import ipaddr
import simplejson as json


class RangeView(object):
    model = Range
    form_class = RangeForm
    queryset = Range.objects.all()


class RangeDeleteView(RangeView, CoreDeleteView):
    pass


class RangeCreateView(RangeView, CoreCreateView):
    def get_form(self, form_class):
        if not self.request.POST:
            initial = {}
            initial.update(dict(self.request.GET.items()))
            return form_class(initial=initial)
        else:
            return super(RangeCreateView, self).get_form(form_class)


class RangeUpdateView(RangeView, CoreUpdateView):
    template_name = "range/range_edit.html"


class RangeListView(RangeView, CoreListView):
    template_name = "range/range_list.html"


class RangeDetailView(RangeView, CoreDetailView):
    template_name = 'range/range_detail.html'

    def get_context_data(self, **kwargs):
        context = super(RangeDetailView, self).get_context_data(
            **kwargs)
        context['form_title'] = "{0} Details".format(
            self.form_class.Meta.model.__name__
        )

        # extra_context takes precedence over original values in context
        if self.extra_context:
            context = dict(context.items() + self.extra_context.items())
        return context


def range_usage_text(request):
    start = request.GET.get('start', None)
    end = request.GET.get('end', None)
    format = request.GET.get('format', 'human_readable')
    if not (start and end):
        return HttpResponse(json.dumps({
            'success': False,
            'error_messages': 'Provide a start and end'}))

    get_objects = request.GET.get('get_objects', False)
    if start.find(':') > -1:
        ip_type = '6'
    else:
        ip_type = '4'
    try:
        usage_data = range_usage(start, end, ip_type, get_objects)
    except (ValidationError, ipaddr.AddressValueError), e:
        return HttpResponse(
            json.dumps({
                'error_messages': str(e),
                'success': False
            }))

    if format == 'human_readable':
        usage_data['free_ranges'] = map(lambda x: (int_to_ip(x[0], ip_type),
                                        int_to_ip(x[1], ip_type)),
                                        usage_data['free_ranges'])

    usage_data['success'] = True
    return HttpResponse(json.dumps(usage_data))


def range_usage_ajax(request):
    start = request.GET.get('start', None)
    end = request.GET.get('end', None)
    start_ip_type, _ = resolve_ip_type(start)
    end_ip_type, _ = resolve_ip_type(end)
    errors = None
    if start_ip_type != end_ip_type or start_ip_type is None:
        errors = "Couldn't resolve ip_type"
        return render(request, 'range/range_usage_ajax.html', {
            'errors': errors,
        })
    rusage = range_usage(start, end, start_ip_type, get_objects=True)

    def translate_ip(ip_i, *args):
        return int_to_ip(ip_i, start_ip_type)

    return render(request, 'range/range_usage_ajax.html', {
        'errors': errors,
        'start': start,
        'end': end,
        'start_i': int_to_ip(start, start_ip_type),
        'end_i': int_to_ip(end, end_ip_type),
        'rusage': rusage,
        'translate_ip': translate_ip
    })


def range_detail(request, range_pk):
    mrange = get_object_or_404(Range, pk=range_pk)
    attrs = mrange.keyvalue_set.all()
    return render(request, 'range/range_detail.html', {
        'range': mrange,
        'attrs': attrs,
    })


def redirect_to_range_from_ip(request):
    ip_str = request.GET.get('ip_str')
    ip_type = request.GET.get('ip_type')
    if not (ip_str and ip_type):
        return HttpResponse(json.dumps({'failure': "Slob"}))

    if ip_type == '4':
        try:
            ip_upper, ip_lower = 0, int(ipaddr.IPv4Address(ip_str))
        except ipaddr.AddressValueError:
            return HttpResponse(
                json.dumps({'success': False, 'message': "Failure to "
                           "recognize{0} as an IPv4 "
                           "Address.".format(ip_str)}))
    else:
        try:
            ip_upper, ip_lower = ipv6_to_longs(ip_str)
        except ValidationError:
            return HttpResponse(json.dumps({'success': False,
                                            'message': 'Invalid IP'}))

    range_ = Range.objects.filter(start_upper__lte=ip_upper,
                                  start_lower__lte=ip_lower,
                                  end_upper__gte=ip_upper,
                                  end_lower__gte=ip_lower)
    if not len(range_) == 1:
        return HttpResponse(json.dumps({'failure': "Failture to find range"}))
    else:
        return HttpResponse(json.dumps(
            {'success': True,
             'redirect_url': range_[0].get_absolute_url()}))


def get_next_available_ip_by_range(request, range_id):
    range = get_object_or_404(Range, id=range_id)
    ret = {}
    ret_ip = range.get_next_ip()
    display_ip = ret_ip.exploded
    ret['success'] = True
    ret['ip_str'] = display_ip
    return HttpResponse(json.dumps(ret))


def find_related(request):
    """
    Given a list of site, vlan, and network primary keys, help a user make
    choices about where to put an IP address

    A user can select from choices:
        Networks
        Vlans
        Sites

    The goal of the UI is to help a user choose a range -- which for this
    function can be seen as filtering down to exactly 1 network.

    When a user selects a site, this can limit which networks and in turn which
    vlans are displayed.

    When a user selects a vlan, this can limit which networks are displayed
    which in turn can limit which sites are displayed

    When a user selects a network, this will limit both networks, vlans, and
    sites to at most one object per each type.

    input::
        {
            'choice': [<type>, <pk>],
            'sites': [1, ...],
            'vlans': [1, ...],
            'networks': [1, ...],
        }

    The value of '<type>' is a string that is either 'site', 'vlan', or
    'network'. The value of '<pk>' is a number.

    output:
        Same as input but with things filtered plus a new list of 'range'
        information. E.x.:
        {
            'sites': [<pks>],
            'vlans': [<pks>],
            'networks': [<pks>],
            'range': [
                {'name': ...
                 'ip_start': ...
                 'ip_end': ...
                 'reserved': ...
                },
                ...
                ...
                ...
                {'name': ...
                 'ip_start': ...
                 'ip_end': ...
                 'reserved': ...
                }
            ]
        }

    This function will key off of 'choice' to determine how to slim down a
    users choice of objects.
    """
    state = json.loads(request.raw_post_data)

    if not state:
        raise Exception("No state?")

    if 'choice' not in state:
        raise Exception("No choice?")

    try:
        choice_type, choice_pk = state['choice']
    except ValueError:
        raise Exception(
            "Choice was '{0}'. This is wrong".format(state['choice'])
        )

    filter_network, filter_site, filter_vlan = calculate_filters(
        choice_type, choice_pk
    )
    format_network, format_site, format_vlan = label_value_maker()

    new_state = {
        'sites': format_site(filter_site(state['sites'])),
        'vlans': format_vlan(filter_vlan(state['vlans'])),
    }

    # Network are special. If there is only one, we need to add some range
    # info. If there are zero or more than one, don't add any range objects
    networks = filter_network(state['networks'])
    if len(networks) == 1:
        new_state['ranges'] = integrate_real_ranges(
            networks[0], calc_template_ranges(networks[0])
        )
    new_state['networks'] = format_network(networks)

    return HttpResponse(json.dumps(new_state))


def ajax_find_related(request):
    networks = Network.objects.filter(UN).order_by(
        'ip_type', 'network_str', 'prefixlen'
    )
    return render(request, 'range/ip_chooser.html', {
        'sites': Site.objects.all().order_by('name'),
        'vlans': Vlan.objects.all().order_by('name'),
        'networks': networks
    })


def debug_show_ranges(request):
    """
    List all networks and show their range templates and also include range
    objects. These ranges and templates will show up in the FFIP interface.
    This is a good place to see all of these ranges in one place.
    """
    networks = Network.objects.filter(UN).order_by(
        'ip_type', 'network_str', 'prefixlen'
    )
    return render(request, 'range/debug_show_ranges.html', {
        'calc_template_ranges': calc_template_ranges,
        'networks': networks
    })
