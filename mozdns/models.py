from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models

import mozdns
from mozdns.domain.models import Domain, _check_TLD_condition
from mozdns.view.models import View
from mozdns.mixins import ObjectUrlMixin
from mozdns.validation import validate_first_label, validate_name
from settings import MOZDNS_BASE_URL

import pdb


class MozdnsRecord(models.Model, ObjectUrlMixin):
    """
    This class provides common functionality that many DNS record
    classes share.  This includes a foreign key to the ``domain`` table
    and a ``label`` CharField.  This class also inherits from the
    ``ObjectUrlMixin`` class to provide the ``get_absolute_url``,
    ``get_edit_url``, and ``get_delete_url`` functions.

    This class does validation on the ``label`` field. Call
    ``clean_all`` to trigger the validation functions. Failure to
    validate will raise a ``ValidationError``.

    If you plan on using the ``unique_together`` constraint on a Model
    that inherits from ``MozdnsRecord``, you must include ``domain`` and
    ``label`` explicitly if you need them to.  ``MozdnsRecord`` will not
    enforce uniqueness for you.

    All common records have a ``fqdn`` field. This field is updated
    every time the object is saved::

        fqdn = name + domain.name

        or if name == ''

        fqdn = domain.name

    This field makes searching for records much easier. Instead of
    looking at ``obj.label`` together with ``obj.domain.name``, you can
    just search the ``obj.fqdn`` field.

    As of commit 7b2fd19f, the build scripts do not care about ``fqdn``.
    This could change.

    "the total number of octets that represent a name (i.e., the sum of
    all label octets and label lengths) is limited to 255" - RFC 4471
    """

    domain = models.ForeignKey(Domain, null=False)
    label = models.CharField(max_length=100, blank=True, null=True,
                             validators=[validate_first_label])
    fqdn = models.CharField(max_length=255, blank=True, null=True,
                            validators=[validate_name])
    views = models.ManyToManyField(View)
    # fqdn = label + domain.name <--- see set_fqdn

    class Meta:
        abstract = True

    def clean(self):
        set_fqdn(self)
        check_TLD_condition(self)

    def save(self, *args, **kwargs):
        # Only CNAME uses this kwarg.
        no_build = kwargs.pop('no_build', False)
        super(MozdnsRecord, self).save(*args, **kwargs)
        if no_build:
            pass
        else:
            # Mark the domain as dirty so it can be rebuilt.
            self.domain.dirty = True
            self.domain.save()

    def set_fqdn(self):
        set_fqdn(self)

    def check_for_cname(self):
        check_for_cname(self)

    def check_for_delegation(self):
        check_for_delegation(self)

    def check_TLD_condition(self):
        _check_TLD_condition(self)


#####
def set_fqdn(record):
    try:
        if record.label == '':
            record.fqdn = record.domain.name
        else:
            record.fqdn = "{0}.{1}".format(record.label, record.domain.name)
    except ObjectDoesNotExist:
        return


def check_for_cname(record):
    """"If a CNAME RR is preent at a node, no other data should be
    present; this ensures that the data for a canonical name and its
    aliases cannot be different."

    -- `RFC 1034 <http://tools.ietf.org/html/rfc1034>`_

    Call this function in models that can't overlap with an existing
    CNAME.
    """
    CNAME = mozdns.cname.models.CNAME
    if CNAME.objects.filter(fqdn=record.fqdn).exists():
        raise ValidationError("A CNAME with this name already exists.")


def check_for_delegation(record):
    """If an object's domain is delegated it should not be able to
    be changed.  Delegated domains cannot have objects created in
    them.
    """
    if not record.domain.delegated:
        return
    if not record.pk:  # We don't exist yet.
        raise ValidationError("No objects can be created in the {0}"
                              "domain. It is delegated."
                              .format(record.domain.name))


def check_TLD_condition(record):
    _check_TLD_condition(record)
