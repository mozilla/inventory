from mozdns.utils import slim_form
from base.base.views import BaseListView, BaseDetailView, BaseCreateView
from base.base.views import BaseUpdateView, BaseDeleteView


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
        """This removes the unhelpful "Hold down the...." help texts for the
        specified fields for a form."""
        remove_message = unicode(' Hold down "Control", or "Command" on a Mac,'
                                 'to select more than one.')
        for field in form.fields:
            if field in form.base_fields:
                if form.base_fields[field].help_text:
                    new_text = form.base_fields[field].help_text.replace(
                        remove_message, '')
                    new_text = new_text.strip()
                    form.base_fields[field].help_text = new_text
        return form


class MozdnsUpdateView(BaseUpdateView):
    template_name = 'mozdns/mozdns_form.html'

    def get_form(self, form_class):
        form = super(MozdnsUpdateView, self).get_form(form_class)
        """This removes the unhelpful "Hold down the...." help texts for the
        specified fields for a form."""
        remove_message = unicode(' Hold down "Control", or "Command" on a Mac,'
                                 'to select more than one.')
        for field in form.fields:
            if field in form.base_fields:
                if form.base_fields[field].help_text:
                    new_text = form.base_fields[field].help_text.replace(
                        remove_message, '')
                    new_text = new_text.strip()
                    form.base_fields[field].help_text = new_text
        return form


class MozdnsDeleteView(BaseDeleteView):
    """ """
    template_name = 'mozdns/mozdns_confirm_delete.html'
    succcess_url = '/mozdns/'
