from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import m2m_changed

import mozdns
from mozdns.domain.models import Domain, _check_TLD_condition
from mozdns.view.models import View
from mozdns.mixins import ObjectUrlMixin
from mozdns.validation import validate_first_label, validate_name
from mozdns.validation import validate_ttl, is_rfc1918, is_rfc4193
from settings import MOZDNS_BASE_URL

import pdb

@receiver(m2m_changed)
def views_handler(sender, **kwargs):
    """ This function catches any changes to a manymany relationship and just nukes
    the relationship to the "private" view if one exists.

    One awesome side affect of this hack is there is NO way for this function
    to relay that there was an error to the user. If we want to tell the user
    that we nuked the record's relationship to the public view we will need to
    do that in a form.
    """
    if kwargs["action"] != "post_add":
        return
    instance = kwargs.pop("instance", None)
    if (not instance or not hasattr(instance, "ip_str") or
            not hasattr(instance, "ip_type")):
        return
    model = kwargs.pop("model", None)
    if not View == model:
        return
    if instance.views.filter(name="public").exists():
        if instance.ip_type == '4' and is_rfc1918(instance.ip_str):
            instance.views.remove(View.objects.get(name="public"))
        elif instance.ip_type == '6' and is_rfc4193(instance.ip_str):
            instance.views.remove(View.objects.get(name="public"))

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

    "the total number of octets that represent a name (i.e., the sum of
    all label octets and label lengths) is limited to 255" - RFC 4471
    """

    domain = models.ForeignKey(Domain, null=False)
    label = models.CharField(max_length=100, blank=True, null=True,
                             validators=[validate_first_label])
    fqdn = models.CharField(max_length=255, blank=True, null=True,
                            validators=[validate_name])
    ttl = models.PositiveIntegerField(default=3600, blank=True, null=True,
            validators=[validate_ttl])
    views = models.ManyToManyField(View)
    comment = models.CharField(max_length=1000, blank=True, null=True)
    # fqdn = label + domain.name <--- see set_fqdn

    class Meta:
        abstract = True

    def clean(self):
        set_fqdn(self)
        check_TLD_condition(self)

    def save(self, *args, **kwargs):
        # Only CNAME uses this kwarg.
        no_build = kwargs.pop("no_build", False)
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
