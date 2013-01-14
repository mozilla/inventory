from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models

import mozdns
from mozdns.domain.models import Domain, _check_TLD_condition
from mozdns.view.models import View
from mozdns.mixins import ObjectUrlMixin, DisplayMixin
from mozdns.validation import validate_first_label, validate_name
from mozdns.validation import validate_ttl


class MozdnsRecord(models.Model, DisplayMixin, ObjectUrlMixin):
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

    domain = models.ForeignKey(Domain, null=False, help_text="FQDN of the "
                "domain after the short hostname. "
                "(Ex: <i>Vlan</i>.<i>DC</i>.mozilla.com)")
    # "The length of any one label is limited to between 1 and 63 octets."
    # RFC218
    label = models.CharField(max_length=63, blank=True, null=True,
                validators=[validate_first_label],
                help_text="Short name of the fqdn")
    fqdn = models.CharField(max_length=255, blank=True, null=True,
                validators=[validate_name], db_index=True)
    ttl = models.PositiveIntegerField(default=3600, blank=True, null=True,
            validators=[validate_ttl],
            help_text="Time to Live of this record")
    views = models.ManyToManyField(View, blank=True)
    description = models.CharField(max_length=1000, blank=True, null=True,
                help_text="A description of this record.")
    # fqdn = label + domain.name <--- see set_fqdn

    class Meta:
        abstract = True

    @classmethod
    def get_api_fields(cls):
        """The purpose of this is to help the API decide which fields to expose
        to the user when they are creating and updateing an Object. This
        function should be implemented in inheriting models and overriden to
        provide additional fields. Tastypie ignores any relational fields on
        the model. See the ModelResource definitions for view and domain
        fields.
        """
        return ['fqdn', 'ttl', 'description', 'views']

    def clean(self):
        self.set_fqdn()
        self.check_TLD_condition()
        self.check_no_ns_soa_condition()
        self.check_for_delegation()

    def delete(self, *args, **kwargs):
        from mozdns.utils import prune_tree
        objs_domain = self.domain
        super(MozdnsRecord, self).delete(*args, **kwargs)
        prune_tree(objs_domain)

    def save(self, *args, **kwargs):
        if self.pk:
            # We need to get the domain from the db. If it's not our current
            # domain, call prune_tree on the domain in the db later.
            db_domain = self.__class__.objects.get(pk=self.pk).domain
            if self.domain == db_domain:
                db_domain = None
        else:
            db_domain = None
        no_build = kwargs.pop("no_build", False)
        super(MozdnsRecord, self).save(*args, **kwargs)
        if no_build:
            pass
        else:
            # Mark the soa
            if self.domain.soa:
                self.domain.soa.dirty = True
                self.domain.soa.save()
        if db_domain:
            from mozdns.utils import prune_tree
            prune_tree(db_domain)

    def set_fqdn(self):
        set_fqdn(self)

    def check_for_cname(self):
        check_for_cname(self)

    def check_TLD_condition(self):
        _check_TLD_condition(self)

    def check_no_ns_soa_condition(self):
        check_no_ns_soa_condition(self)

    def check_for_delegation(self):
        check_for_delegation(self)


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
    if hasattr(record, 'label'):
        if CNAME.objects.filter(domain=record.domain,
                label=record.label).exists():
            raise ValidationError("A CNAME with this name already exists.")
    else:
        if CNAME.objects.filter(label='', domain=record.domain).exists():
            raise ValidationError("A CNAME with this name already exists.")

def check_for_delegation(record):
    """If an object's domain is delegated it should not be able to
    be changed.  Delegated domains cannot have objects created in
    them.
    """
    try:
        if not record.domain.delegated:
            return
    except ObjectDoesNotExist:
        return
    if not record.pk:  # We don't exist yet.
        raise ValidationError("No objects can be created in the {0}"
                              "domain. It is delegated."
                              .format(record.domain.name))


def check_TLD_condition(record):
    _check_TLD_condition(record)


def check_no_ns_soa_condition(record):
    if record.domain.soa:
        root_domain = record.domain.soa.root_domain
        if root_domain and not root_domain.nameserver_set.exists():
            raise ValidationError("The zone you are trying to assign this "
                    "record into does not have an NS record, thus cannnot "
                    "support other records.")


