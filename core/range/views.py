from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.http import HttpResponse

from core.utils import int_to_ip, resolve_ip_type
from core.range.forms import RangeForm
from core.range.utils import range_usage
from core.range.models import Range
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
    pass


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
    ret['ip_address'] = display_ip
    return HttpResponse(json.dumps(ret))


def get_all_ranges_ajax(request):
    system_pk = request.GET.get('system_pk', '-1')
    location = None
    system = None
    ret_list = []
    from systems.models import System
    try:
        system = System.objects.get(pk=system_pk)
    except ObjectDoesNotExist:
        pass
    if system:
        try:
            location = system.system_rack.location.name.title()
        except AttributeError:
            pass

    for r in Range.objects.all().order_by('network__site'):
        relevant = False
        if r.network.site:
            site_name = r.network.site.get_site_path()
            if location and location == r.network.site.name.title():
                relevant = True
        else:
            site_name = ''

        if r.network.vlan:
            vlan_name = r.network.vlan.name
        else:
            vlan_name = ''

        ret_list.append({'id': r.pk,
                         'display': r.choice_display(),
                         'vlan': vlan_name,
                         'site': site_name,
                         'relevant': relevant
                         })
    return HttpResponse(json.dumps(ret_list))
