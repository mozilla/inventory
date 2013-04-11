from django.shortcuts import get_object_or_404
from django.shortcuts import render

from core.vlan.models import Vlan
from core.vlan.forms import VlanForm

from core.views import (
    CoreDeleteView, CoreListView, CoreCreateView, CoreUpdateView
)


class VlanView(object):
    model = Vlan
    queryset = Vlan.objects.all()
    form_class = VlanForm


class VlanDeleteView(VlanView, CoreDeleteView):
    pass


class VlanListView(VlanView, CoreListView):
    template_name = "vlan/vlan_list.html"


class VlanCreateView(VlanView, CoreCreateView):
    template_name = "core/core_form.html"


class VlanUpdateView(VlanView, CoreUpdateView):
    template_name = "vlan/vlan_edit.html"


def vlan_detail(request, vlan_pk):
    vlan = get_object_or_404(Vlan, pk=vlan_pk)
    attrs = vlan.keyvalue_set.all()
    return render(request, "vlan/vlan_detail.html", {
        "vlan": vlan,
        "attrs": attrs
    })
