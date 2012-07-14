from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.http import HttpResponse


from core.range.forms import RangeForm
from core.range.models import Range, RangeKeyValue
from core.interface.static_intr.models import StaticInterface
from mozdns.address_record.models import AddressRecord
from mozdns.ptr.models import PTR
from core.views import CoreDeleteView, CoreDetailView
from core.views import CoreCreateView, CoreUpdateView, CoreListView
from core.keyvalue.utils import get_attrs, update_attrs, get_aa, get_docstrings
from core.keyvalue.utils import get_docstrings
from django.forms.util import ErrorList, ErrorDict

import ipaddr
import simplejson as json
import pdb

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

def range_detail(request, range_pk):
    mrange = get_object_or_404(Range, pk=range_pk)
    attrs = mrange.rangekeyvalue_set.all()

    start = mrange.start
    end = mrange.end
    records = AddressRecord.objects.filter(ip_upper = 0, ip_lower__gte = start,
            ip_lower__lte = end)
    ptrs = PTR.objects.filter(ip_upper = 0, ip_lower__gte = start,
            ip_lower__lte = end)
    intrs = StaticInterface.objects.filter(ip_upper = 0, ip_lower__gte = start,
            ip_lower__lte = end)

    range_data = []
    # This won't work for IPv6 yet.
    for i in range(start + 10, end-1):
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

        if taken == False:
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
                if form._errors is None:
                    form._errors = ErrorDict()
                form._errors['__all__'] = ErrorList(e.messages)
                return render(request, 'range/range_edit.html', {
                    'range': mrange,
                    'form': form,
                    'attrs': attrs,
                    'docs': docs,
                    'aa': json.dumps(aa)
                })
            else:
                # Handle key value stuff.
                kv = get_attrs(request.POST)
                update_attrs(kv, attrs, RangeKeyValue, mrange, 'range')
                mrange = form.save()
                return redirect(mrange.get_edit_url())
        except ValidationError, e:
            if form._errors is None:
                form._errors = ErrorDict()
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


class RangeUpdateView(RangeView, CoreUpdateView):
    """ """


class RangeListView(RangeView, CoreListView):
    """ """
