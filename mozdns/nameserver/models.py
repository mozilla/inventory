from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from mozdns.domain.models import Domain
from mozdns.address_record.models import AddressRecord
from mozdns.validation import validate_label, validate_name
from mozdns.models import MozdnsRecord
from mozdns.view.models import View

from core.registration.static.models import StaticReg

import reversion

from string import Template


class Nameserver(MozdnsRecord):
    """Name server for forward domains::

        >>> Nameserver(domain = domain, server = server)

        Sometimes a name server needs a glue record. A glue record can either
        be an AddressRecord or a StaticReg. These two types are
        represented by the attributes `addr_glue` and `sreg_glue`, which are
        both FK's enforced by the DB.

        If there are multiple A or Registrations that fit the criterion of
        being an NS's glue record, the user should have the choice to choose
        between records. Because of this, a glue record will only be
        automatically assigned to a NS if a) The NS doesn't have a glue record
        or b) the glue record the NS has isn't valid.
    """
    id = models.AutoField(primary_key=True)
    domain = models.ForeignKey(
        Domain, null=False, help_text="The domain this record is for."
    )
    server = models.CharField(
        max_length=255, validators=[validate_name], help_text="The name of "
        "the server this records points to."
    )
    # "If the name server does lie within the domain it should have a
    # corresponding A record."
    addr_glue = models.ForeignKey(AddressRecord, null=True, blank=True,
                                  related_name="nameserver_set")
    sreg_glue = models.ForeignKey(StaticReg, null=True, blank=True,
                                  related_name="nameserver_set")

    template = ("{bind_name:$lhs_just} {ttl_} {rdclass:$rdclass_just} "
                "{rdtype:$rdtype_just} {server:$rhs_just}.")

    search_fields = ("server", "domain__name")

    def __str__(self):
        return self.bind_render_record()

    class Meta:
        db_table = "nameserver"
        unique_together = ("domain", "server")

    @classmethod
    def get_api_fields(cls):
        return ['ttl', 'description', 'server', 'domain', 'views']

    @property
    def rdtype(self):
        return 'NS'

    def bind_render_record(self, pk=False, show_ttl=False, **kwargs):
        # We need to override this because fqdn is actually self.domain.name
        if show_ttl:
            ttl_ = self.ttl
        else:
            ttl_ = '' if self.ttl is None else self.ttl
        template = Template(self.template).substitute(**self.justs)
        return template.format(
            rdtype=self.rdtype, rdclass='IN', bind_name=self.domain.name + '.',
            ttl_=ttl_, **vars(self)
        )

    def details(self):
        return (
            ("Server", self.server),
            ("Domain", self.domain.name),
            ("Glue", self.get_glue()),
        )

    def save(self, *args, **kwargs):
        no_build = kwargs.pop('no_build', False)
        super(Nameserver, self).save(*args, **kwargs)
        # We have to full build here because changing the views on a
        # nameserver can actually cause a zone to not be emitted, which we need
        # to account for in the builds.
        if not no_build:  # XXX fuck, double negative... must've been drunk
            if self.domain.soa:
                self.domain.soa.schedule_full_rebuild()

    def get_glue(self):
        if self.addr_glue:
            return self.addr_glue
        elif self.sreg_glue:
            return self.sreg_glue
        else:
            return None

    def set_glue(self, glue):
        if isinstance(glue, AddressRecord):
            self.addr_glue = glue
            self.sreg_glue = None
        elif isinstance(glue, StaticReg):
            self.addr_glue = None
            self.sreg_glue = glue
        elif isinstance(glue, type(None)):
            self.addr_glue = None
            self.sreg_glue = None
        else:
            raise ValueError(
                "Cannot assign {0}: Nameserver.glue must be of either type "
                "AddressRecord or type StaticReg.".format(glue)
            )

    def del_glue(self):
        if self.addr_glue:
            self.addr_glue.delete()
        elif self.sreg_glue:
            self.sreg_glue.delete()
        else:
            raise AttributeError("'Nameserver' object has no attribute 'glue'")

    glue = property(get_glue, set_glue, del_glue, "The Glue property.")

    def delete(self, *args, **kwargs):
        no_build = kwargs.pop('no_build', False)
        if self.domain.soa:
            soa = self.domain.soa
        else:
            soa = None
        self.check_no_ns_soa_condition(self.domain)
        super(Nameserver, self).delete(*args, **kwargs)
        if not no_build and soa:
            # XXX fuck, double negative... must've been drunk
            soa.schedule_full_rebuild()

    def clean(self):
        # We are a MozdnsRecord, our clean method is called during save()!
        self.check_for_cname()
        self.check_for_illegal_rr_ttl(
            field_name='domain__name', rr_value=self.domain.name
        )

        if not self.needs_glue():
            self.glue = None
        else:
            # Try to find any glue record. It will be the first elligible
            # The resolution is:
            #  * Address records are searched.
            #  * Registration records are searched.
            # AddressRecords take higher priority over registration records.
            glue_label = self.server.split('.')[0]  # foo.com -> foo
            if not (self.glue and self.glue.label == glue_label and
                    self.glue.domain == self.domain):
                # Ok, our glue record wasn't valid, let's find a new one.
                addr_glue = AddressRecord.objects.filter(
                    label=glue_label, domain=self.domain
                )
                sreg_glue = StaticReg.objects.filter(
                    label=glue_label, domain=self.domain
                )
                if not (addr_glue or sreg_glue):
                    raise ValidationError(
                        "This NS needs a glue record. Create a glue "
                        "record for the server before creating "
                        "the NS record."
                    )
                else:
                    if addr_glue:
                        self.glue = addr_glue[0]
                    else:
                        self.glue = sreg_glue[0]

    def clean_views(self, views):
        # Forms will call this function with the set of views it is about to
        # set on this object. Make sure we aren't serving as the NS for a view
        # that we are about to remove.
        removed_views = set(View.objects.all()) - set(views)
        for view in removed_views:
            if (self.domain.soa and
                self.domain.soa.root_domain == self.domain and
                self.domain.nameserver_set.filter(views=view).count() == 1 and
                # We are it!
                    self.domain.soa.has_record_set(exclude_ns=True,
                                                   view=view)):
                raise ValidationError(
                    "Other records in this nameserver's zone are "
                    "relying on it's existance in the {0} view. You can't "
                    "remove it's memebership of the {0} view.".format(view)
                )

    def check_no_ns_soa_condition(self, domain):
        # XXX hmm, is this redundant?
        if (domain.soa and
            domain.soa.root_domain == domain and
            domain.nameserver_set.count() == 1 and  # We are it!
                domain.soa.has_record_set(exclude_ns=True)):
            raise ValidationError(
                "Other records in this nameserver's zone are "
                "relying on it's existance as it is the only nameserver "
                "at the root of the zone."
            )

    def needs_glue(self):
        # Replace the domain portion of the server with "".
        # if domain == foo.com and server == ns1.foo.com.
        #       ns1.foo.com --> ns1
        try:
            possible_label = self.server.replace("." + self.domain.name, "")
        except ObjectDoesNotExist:
            return False

        if possible_label == self.server:
            return False
        try:
            validate_label(possible_label)
        except ValidationError:
            # It's not a valid label
            return False
        return True

reversion.register(Nameserver)
