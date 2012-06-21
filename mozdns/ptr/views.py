from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render

from mozdns.views import MozdnsCreateView
from mozdns.views import MozdnsDeleteView
from mozdns.views import MozdnsDetailView
from mozdns.views import MozdnsListView
from mozdns.views import MozdnsUpdateView
from mozdns.ip.forms import IpForm
from mozdns.ptr.forms import PTRForm
from mozdns.ptr.models import PTR


class PTRView(object):
    model = PTR
    form_class = PTRForm
    queryset = PTR.objects.all()


class PTRDeleteView(PTRView, MozdnsDeleteView):
    """ """


class PTRDetailView(PTRView, MozdnsDetailView):
    """ """
    template_name = "ptr/ptr_detail.html"


class PTRCreateView(PTRView, MozdnsCreateView):
    """ """


class PTRUpdateView(PTRView, MozdnsUpdateView):
    """ """


class PTRListView(PTRView, MozdnsListView):
    """ """
