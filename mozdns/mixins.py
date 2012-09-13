from settings import MOZDNS_BASE_URL
from gettext import gettext as _


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
        """
        Return the absolute url of an object.
        """
        return MOZDNS_BASE_URL + "/{0}/{1}/".format(
            self._meta.db_table, self.pk
        )

    def absolute_url(self):
        return self.get_absolute_url()

    def get_edit_url(self):
        """
        Return the edit url of an object.
        """
        return MOZDNS_BASE_URL + "/{0}/{1}/update/".format(
            self._meta.db_table, self.pk
        )

    def get_fancy_edit_url(self):
        return MOZDNS_BASE_URL + _("/record/"
            "?record_type={0}&record_pk={1}").format(self.rdtype, self.pk)

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
