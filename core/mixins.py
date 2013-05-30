from settings import CORE_BASE_URL


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
        return CORE_BASE_URL + "/{0}/{1}/".format(
            self._meta.db_table, self.pk
        )

    # TODO, depricate this
    def get_edit_url(self):
        """
        Return the edit url of an object.
        """
        return CORE_BASE_URL + "/{0}/{1}/update/".format(
            self._meta.db_table, self.pk
        )

    def edit_url(self):
        """
        Return the edit url of an object.
        """
        return CORE_BASE_URL + "/{0}/{1}/update/".format(
            self._meta.db_table, self.pk
        )

    def get_delete_url(self):
        """
        Return the delete url of an object.
        """
        return CORE_BASE_URL + "/{0}/{1}/delete/".format(
            self._meta.db_table, self.pk
        )

    def get_create_url(self):
        """
        Return the create url of the type of object.
        """
        return CORE_BASE_URL + "/{0}/create/".format(self._meta.db_table)


class RangeProperty(object):
    @property
    def range(self):
        if hasattr(self, '_memoize_ip_str'):
            if self._memoize_ip_str == self.ip_str:
                return self._memoize_range
        from core.range.utils import ip_to_range
        self._memoize_ip_str = self.ip_str
        self._memoize_range = ip_to_range(self.ip_str)
        return self._memoize_range
