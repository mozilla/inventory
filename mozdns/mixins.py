from settings import MOZDNS_BASE_URL
from gettext import gettext as _
from string import Template


class DisplayMixin(object):
    # Knobs
    justs = {
        'pk_just': 10,
        'rhs_just': 1,
        'ttl_just': 1,
        'rdtype_just': 4,
        'rdclass_just': 3,
        'prio_just': 1,
        'lhs_just': 40,
        'extra_just': 1
    }

    def bind_render_record(self, pk=False, show_ttl=False):
        template = Template(self.template).substitute(**self.justs)
        bind_name = self.fqdn + "."
        if show_ttl:
            ttl_ = self.ttl
        else:
            ttl_ = '' if self.ttl is None else self.ttl
        return template.format(
            bind_name=bind_name, rdtype=self.rdtype, rdclass='IN',
            ttl_=ttl_, **vars(self)
        )


class ObjectUrlMixin(object):
    """
    This is a mixin that adds important url methods to a model. This
    class uses the ``_meta.db_table`` instance variable of an object to
    calculate URLs. Because of this, you must use the app label of your
    class when declaring urls in your urls.py.
    """
    # TODO. using app_label breaks shit. Go through all the models and
    # assign a better field.  Something like "url handle".  TODO2. Using
    # db_table for now. It looks weird, but it works.
    def get_absolute_url(self):
        return self.get_fancy_edit_url()

    def get_history_url(self):
        return "/reversion_compare/history_view/{0}/{1}/".format(
            self.rdtype, self.pk
        )

    def get_edit_url(self):
        """
        Return the edit url of an object.
        """
        return self.get_fancy_edit_url()

    def get_fancy_edit_url(self):
        return MOZDNS_BASE_URL + _(
            "/record/update/{0}/{1}/").format(self.rdtype, self.pk)

    def get_delete_url(self):
        """
        Return the delete url of an object.
        """
        return MOZDNS_BASE_URL + "/{0}/{1}/delete/".format(
            self._meta.db_table, self.pk
        )

    def get_create_url(self):
        """
        Return the create url of the type of object.
        """
        return MOZDNS_BASE_URL + "/{0}/create/".format(self._meta.db_table)

    def get_delete_redirect_url(self):
        return '/core/search/'


class DBTableURLMixin(object):
    def get_fancy_edit_url(self):
        return self.get_edit_url()

    def get_edit_url(self):
        """
        Return the delete url of an object.
        """
        return MOZDNS_BASE_URL + "/{0}/{1}/update/".format(
            self._meta.db_table, self.pk
        )

    def get_delete_url(self):
        """
        Return the delete url of an object.
        """
        return MOZDNS_BASE_URL + "/{0}/{1}/delete/".format(
            self._meta.db_table, self.pk
        )

    def get_absolute_url(self):
        """
        Return the delete url of an object.
        """
        return MOZDNS_BASE_URL + "/{0}/{1}/".format(
            self._meta.db_table, self.pk
        )

    def get_create_url(self):
        """
        Return the create url of the type of object.
        """
        return MOZDNS_BASE_URL + "/{0}/create/".format(self._meta.db_table)
