from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models

import mozdns
from mozdns.domain.models import Domain
from mozdns.view.models import View
from mozdns.mixins import ObjectUrlMixin, DisplayMixin
from mozdns.validation import validate_first_label, validate_name
from mozdns.validation import validate_ttl


class LabelDomainMixin(models.Model):
    """
    This class provides common functionality that many DNS record
    classes share.  This includes a foreign key to the ``domain`` table
    and a ``label`` CharField.

    If you plan on using the ``unique_together`` constraint on a Model
    that inherits from ``LabelDomainMixin``, you must include ``domain`` and
    ``label`` explicitly if you need them to.

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
    # -- RFC218
    label = models.CharField(max_length=63, blank=True, null=True,
                             validators=[validate_first_label],
                             help_text="Short name of the fqdn")
    fqdn = models.CharField(max_length=255, blank=True, null=True,
                            validators=[validate_name], db_index=True)

    class Meta:
        abstract = True


class ViewMixin(models.Model):
    def validate_views(instance, views):
        for view in views:
            instance.clean_views(views)

    views = models.ManyToManyField(
        View, blank=True, validators=[validate_views]
    )

    class Meta:
        abstract = True

    def clean_views(self, views):
        """cleaned_data is the data that is going to be called with for
        updating an existing or creating a new object. Classes should implement
        this function according to their specific needs.
        """
        for view in views:
            if hasattr(self, 'domain'):
                self.check_no_ns_soa_condition(self.domain, view=view)
            if hasattr(self, 'reverse_domain'):
                self.check_no_ns_soa_condition(self.reverse_domain, view=view)

    def check_no_ns_soa_condition(self, domain, view=None):
        if domain.soa:
            fail = False
            root_domain = domain.soa.root_domain
            if root_domain and not root_domain.nameserver_set.exists():
                fail = True
            elif (view and
                  not root_domain.nameserver_set.filter(views=view).exists()):
                fail = True
            if fail:
                raise ValidationError(
                    "The zone you are trying to assign this record into does "
                    "not have an NS record, thus cannnot support other "
                    "records.")


class MozdnsRecord(ViewMixin, DisplayMixin, ObjectUrlMixin):
    ttl = models.PositiveIntegerField(default=3600, blank=True, null=True,
                                      validators=[validate_ttl],
                                      help_text="Time to Live of this record")
    description = models.CharField(max_length=1000, blank=True, null=True,
                                   help_text="A description of this record.")
    # fqdn = label + domain.name <--- see set_fqdn

    def __str__(self):
        self.set_fqdn()
        return self.bind_render_record()

    def __repr__(self):
        return "<{0} '{1}'>".format(self.rdtype, str(self))

    class Meta:
        abstract = True

    @classmethod
    def get_api_fields(cls):
        """
        The purpose of this is to help the API decide which fields to expose
        to the user when they are creating and updateing an Object. This
        function should be implemented in inheriting models and overriden to
        provide additional fields. Tastypie ignores any relational fields on
        the model. See the ModelResource definitions for view and domain
        fields.
        """
        return ['fqdn', 'ttl', 'description', 'views']

    def clean(self):
        # The Nameserver and subclasses of BaseAddressRecord do not call this
        # function
        self.set_fqdn()
        self.check_TLD_condition()
        self.check_no_ns_soa_condition(self.domain)
        self.check_for_delegation()
        if self.rdtype != 'CNAME':
            self.check_for_cname()

    def delete(self, *args, **kwargs):
        if self.domain.soa:
            self.domain.soa.schedule_rebuild()

        from mozdns.utils import prune_tree
        call_prune_tree = kwargs.pop('call_prune_tree', True)
        objs_domain = self.domain

        super(MozdnsRecord, self).delete(*args, **kwargs)

        if call_prune_tree:
            prune_tree(objs_domain)

    def save(self, *args, **kwargs):
        self.full_clean()

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
                self.domain.soa.schedule_rebuild()

        if db_domain:
            from mozdns.utils import prune_tree
            prune_tree(db_domain)

    def set_fqdn(self):
        try:
            if self.label == '':
                self.fqdn = self.domain.name
            else:
                self.fqdn = "{0}.{1}".format(self.label,
                                             self.domain.name)
        except ObjectDoesNotExist:
            return

    def check_for_cname(self):
        """
        "If a CNAME RR is preent at a node, no other data should be
        present; this ensures that the data for a canonical name and its
        aliases cannot be different."

        -- `RFC 1034 <http://tools.ietf.org/html/rfc1034>`_

        Call this function in models that can't overlap with an existing
        CNAME.
        """
        CNAME = mozdns.cname.models.CNAME
        if hasattr(self, 'label'):
            if CNAME.objects.filter(domain=self.domain,
                                    label=self.label).exists():
                raise ValidationError("A CNAME with this name already exists.")
        else:
            if CNAME.objects.filter(label='', domain=self.domain).exists():
                raise ValidationError("A CNAME with this name already exists.")

    def check_for_delegation(self):
        """
        If an object's domain is delegated it should not be able to
        be changed.  Delegated domains cannot have objects created in
        them.
        """
        try:
            if not self.domain.delegated:
                return
        except ObjectDoesNotExist:
            return
        if not self.pk:  # We don't exist yet.
            raise ValidationError("No objects can be created in the {0}"
                                  "domain. It is delegated."
                                  .format(self.domain.name))

    def check_TLD_condition(self):
        domain = Domain.objects.filter(name=self.fqdn)
        if not domain:
            return
        if self.label == '' and domain[0] == self.domain:
            return  # This is allowed
        else:
            raise ValidationError("You cannot create an record that points "
                                  "to the top level of another domain.")
