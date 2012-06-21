from mozdns.domain.models import Domain
from mozdns.utils import slim_form
from base.mozdns.views import BaseListView, BaseDetailView, BaseCreateView
from base.mozdns.views import BaseUpdateView, BaseDeleteView


class MozdnsListView(BaseListView):
    """ """
    template_name = 'mozdns/mozdns_list.html'


class MozdnsDetailView(BaseDetailView):
    """ """
    template_name = 'mozdns/mozdns_detail.html'


class MozdnsCreateView(BaseCreateView):
    """ """
    template_name = 'mozdns/mozdns_form.html'

    def get_form(self, form_class):
        form = super(MozdnsCreateView, self).get_form(form_class)
        domain_pk = self.kwargs.get('domain', False)

        # The use of slim_form makes my eyes bleed and stomach churn.
        if domain_pk:
            form = slim_form(domain_pk=domain_pk, form=form)

        reverse_domain_pk = self.kwargs.get('reverse_domain', False)
        if reverse_domain_pk:
            slim_form(reverse_domain_pk=reverse_domain_pk, form=form)

        # This is where filtering domain selection should take place.
        # form.fields['domain'].queryset = Domain.objects.filter(name =
        # 'foo.com') This ^ line will change the query set to something
        # controllable find user credentials in self.request
        return form


class MozdnsUpdateView(BaseUpdateView):
    """ """
    template_name = 'mozdns/mozdns_form.html'


class MozdnsDeleteView(BaseDeleteView):
    """ """
    template_name = 'mozdns/mozdns_confirm_delete.html'
    succcess_url = '/mozdns/'

