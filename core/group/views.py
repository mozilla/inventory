from django.shortcuts import get_object_or_404
from django.shortcuts import render

from core.group.models import Group
from core.group.forms import GroupForm

from core.views import (
    CoreDeleteView, CoreListView, CoreCreateView, CoreUpdateView
)


class GroupView(object):
    model = Group
    queryset = Group.objects.all()
    form_class = GroupForm


class GroupDeleteView(GroupView, CoreDeleteView):
    pass


class GroupListView(GroupView, CoreListView):
    template_name = "core/core_list.html"


class GroupCreateView(GroupView, CoreCreateView):
    template_name = "core/core_form.html"


class GroupUpdateView(GroupView, CoreUpdateView):
    template_name = "group/group_edit.html"


def group_detail(request, group_pk):
    group = get_object_or_404(Group, pk=group_pk)
    attrs = group.keyvalue_set.all()
    return render(request, "group/group_detail.html", {
        "group": group,
        "attrs": attrs
    })
