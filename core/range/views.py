from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.http import HttpResponse

from core.utils import int_to_ip
from core.range.forms import RangeForm
from core.range.utils import range_usage
from core.range.models import Range, RangeKeyValue
from core.interface.static_intr.models import StaticInterface
from mozdns.address_record.models import AddressRecord
from mozdns.ptr.models import PTR
from mozdns.ip.models import ipv6_to_longs
from core.views import CoreDeleteView, CoreDetailView
from core.views import CoreCreateView, CoreUpdateView, CoreListView
from core.keyvalue.utils import get_attrs, update_attrs, get_aa, get_docstrings
from core.keyvalue.utils import dict_to_kv
from django.forms.util import ErrorList, ErrorDict

import ipaddr
import simplejson as json


class RangeView(object):
    model = Range
    form_class = RangeForm
    queryset = Range.objects.all()


class RangeDeleteView(RangeView, CoreDeleteView):
    """ """


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


def delete_range_attr(request, attr_pk):
    """
    An view destined to be called by ajax to remove an attr.
    """
    attr = get_object_or_404(RangeKeyValue, pk=attr_pk)
    attr.delete()
    return HttpResponse("Attribute Removed.")


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


def range_detail(request, range_pk):
    mrange = get_object_or_404(Range, pk=range_pk)
    attrs = mrange.rangekeyvalue_set.all()

    start_upper, start_lower = mrange.start_upper, mrange.start_lower
    end_upper, end_lower = mrange.end_upper, mrange.end_lower

    gt_start = Q(ip_upper=start_upper, ip_lower__gte=start_lower)
    gt_start = gt_start | Q(ip_upper__gte=start_upper)

    lt_end = Q(ip_upper=end_upper, ip_lower__lte=end_lower)
    lt_end = lt_end | Q(ip_upper__lte=end_upper)

    records = AddressRecord.objects.filter(gt_start, lt_end)
    ptrs = PTR.objects.filter(gt_start, lt_end)
    intrs = StaticInterface.objects.filter(gt_start, lt_end)

    range_data = []
    for i in range((start_upper << 64) + start_lower, (end_upper << 64) +
                   end_lower - 1):
        taken = False
        adr_taken = None
        ip_str = str(ipaddr.IPv4Address(i))
        for record in records:
            if record.ip_lower == i:
                adr_taken = record
                break

        ptr_taken = None
        for ptr in ptrs:
            if ptr.ip_lower == i:
                ptr_taken = ptr
                break

        if ptr_taken and adr_taken:
            if ptr_taken.name == adr_taken.fqdn:
                range_data.append(('A/PTR', ip_str, ptr_taken, adr_taken))
            else:
                range_data.append(('PTR', ip_str, ptr_taken))
                range_data.append(('A', ip_str, adr_taken))
            taken = True
        elif ptr_taken and not adr_taken:
            range_data.append(('PTR', ip_str, ptr_taken))
            taken = True
        elif not ptr_taken and adr_taken:
            range_data.append(('A', ip_str, adr_taken))
            taken = True

        for intr in intrs:
            if intr.ip_lower == i:
                range_data.append(('Interface', ip_str, intr))
                taken = True
                break

        if not taken:
            range_data.append((None, ip_str))

    return render(request, 'range/range_detail.html', {
        'range': mrange,
        'attrs': attrs,
        'range_data': range_data
    })


class RangeCreateView(RangeView, CoreCreateView):
    """ """


def update_range(request, range_pk):
    mrange = get_object_or_404(Range, pk=range_pk)
    attrs = mrange.rangekeyvalue_set.all()
    docs = get_docstrings(RangeKeyValue())
    aa = get_aa(RangeKeyValue())
    if request.method == 'POST':
        form = RangeForm(request.POST, instance=mrange)
        try:
            if not form.is_valid():
                return render(request, 'range/range_edit.html', {
                    'range': mrange,
                    'form': form,
                    'attrs': attrs,
                    'docs': docs,
                    'aa': json.dumps(aa)
                })
            else:
                # Handle key value stuff.
                kv = None
                kv = get_attrs(request.POST)
                update_attrs(kv, attrs, RangeKeyValue, mrange, 'range')
                mrange = form.save()
                return redirect(mrange.get_edit_url())
        except ValidationError, e:
            if form._errors is None:
                form._errors = ErrorDict()
            if kv:
                attrs = dict_to_kv(kv, RangeKeyValue)
            form._errors['__all__'] = ErrorList(e.messages)
            return render(request, 'range/range_edit.html', {
                'range': mrange,
                'form': form,
                'attrs': attrs,
                'docs': docs,
                'aa': json.dumps(aa)
            })
    else:
        form = RangeForm(instance=mrange)
        return render(request, 'range/range_edit.html', {
            'range': mrange,
            'form': form,
            'attrs': attrs,
            'docs': docs,
            'aa': json.dumps(aa)
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


class RangeUpdateView(RangeView, CoreUpdateView):
    """ """


class RangeListView(RangeView, CoreListView):
    """ """
