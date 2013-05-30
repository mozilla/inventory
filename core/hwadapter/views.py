from django.http import HttpResponse

from core.hwadapter.forms import HWAdapterForm
from core.hwadapter.models import HWAdapter
from core.views import CoreUpdateView

import simplejson as json


def ajax_hw_adapter_create(request):
    if not request.POST:
        return HttpResponse('Hi')
    form = HWAdapterForm(request.POST, prefix='add-hw')
    if form.is_valid():
        form.save()
        return HttpResponse(json.dumps({'success': True}))
    return HttpResponse(json.dumps({
        'success': False,
        'form': str(form.as_p())
    }))


def ajax_hw_adapter_delete(request, pk):
    try:
        HWAdapter.objects.get(pk=pk).delete()
        return HttpResponse(json.dumps({'success': True}))
    except HWAdapter.DoesNotExist:
        return HttpResponse(json.dumps({
            'success': False,
            'messages': 'Could not find Hardware Adapter with pk '
            '{0}'.format(pk)
        }))


class HWAdapterUpdateView(CoreUpdateView):
    model = HWAdapter
    queryset = HWAdapter.objects.all()
    form_class = HWAdapterForm
