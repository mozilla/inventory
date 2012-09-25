from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from mozdns.domain.models import Domain
from mozdns.address_record.models import AddressRecord
from mozdns.validation import validate_label, validate_name
from mozdns.mixins import ObjectUrlMixin
from mozdns.view.models import View
from mozdns.validation import validate_ttl
from mozdns.models import check_for_cname
from mozdns.soa.utils import update_soa

from core.interface.static_intr.models import StaticInterface

import pdb


class Nameserver(models.Model, ObjectUrlMixin):
    """Name server for forward domains::

        >>> Nameserver(domain = domain, server = server)

        Sometimes a name server needs a glue record. A glue record can either
        be an AddressRecord or a StaticInterface. These two types are
        represented but the attributes `addr_glue` and `intr_glue`, which are
        both FK's enforced by the DB.

        If there are two A or two Interfaces, or one A and one Interface that
        fit the criterion of being a NS's glue record, the user should have the
        choice to choose between records. Because of this, a glue record will
        only be automatically assigned to a NS if a) The NS doesn't have a glue
        record or b) the glue record the NS has isn't valid.
    """
    id = models.AutoField(primary_key=True)
    domain = models.ForeignKey(Domain, null=False, help_text="The domain this "
                "record is for.")
    server = models.CharField(max_length=255, validators=[validate_name],
                help_text="The name of the server this records points to.")
    ttl = models.PositiveIntegerField(default=3600, blank=True, null=True,
            validators=[validate_ttl])
    # "If the name server does lie within the domain it should have a
    # corresponding A record."
    addr_glue = models.ForeignKey(AddressRecord, null=True, blank=True,
            related_name="nameserver_set")
    intr_glue = models.ForeignKey(StaticInterface, null=True, blank=True,
            related_name="intrnameserver_set")
    views = models.ManyToManyField(View, blank=True)
    comment = models.CharField(max_length=1000, null=True, blank=True,
                help_text="Comments about this record.")

    search_fields = ("server",)

    class Meta:
        db_table = "nameserver"
        unique_together = ("domain", "server")

    @classmethod
    def get_api_fields(cls):
        return ['ttl', 'comment', 'server']

    def details(self):
        details = [
            ("Server", self.server),
            ("Domain", self.domain.name),
            ("Glue", self.get_glue()),
        ]
        return tuple(details)

    def delete(self, *args, **kwargs):
        from mozdns.utils import prune_tree
        objs_domain = self.domain
        super(Nameserver, self).delete(*args, **kwargs)
        prune_tree(objs_domain)

    def save(self, *args, **kwargs):
        self.full_clean()
        update_soa(self)
        if self.pk:
            # We need to get the domain from the db. If it's not our current
            # domain, call prune_tree on the domain in the db later.
            db_domain = self.__class__.objects.get(pk=self.pk).domain
            if self.domain == db_domain:
                db_domain = None
        else:
            db_domain = None
        super(Nameserver, self).save(*args, **kwargs)
        if db_domain:
            from mozdns.utils import prune_tree
            prune_tree(db_domain)

    def get_glue(self):
        if self.addr_glue:
            return self.addr_glue
        elif self.intr_glue:
            return self.intr_glue
        else:
            return None

    def set_glue(self, glue):
        if isinstance(glue, AddressRecord):
            self.addr_glue = glue
            self.intr_glue = None
        elif isinstance(glue, StaticInterface):
            self.addr_glue = None
            self.intr_glue = glue
        elif isinstance(glue, type(None)):
            self.addr_glue = None
            self.intr_glue = None
        else:
            raise ValueError("Cannot assing {0}: Nameserver.glue must be of "
                    "either type AddressRecord or type "
                    "StaticInterface.".format(glue))

    def del_glue(self):
        if self.addr_glue:
            self.addr_glue.delete()
        elif self.intr_glue:
            self.intr_glue.delete()
        else:
            raise AttributeError("'Nameserver' object has no attribute 'glue'")

    glue = property(get_glue, set_glue, del_glue, "The Glue property.")

    def clean(self):
        self.check_NS_TLD_condition()
        check_for_cname(self)

        if not self._needs_glue():
            self.glue = None
        else:
            # Try to find any glue record. It will be the first elligible
            # The resolution is:
            #  * Address records are searched.
            #  * Interface records are searched.
            # AddressRecords take higher priority over interface records.
            glue_label = self.server.split('.')[0]  # foo.com -> foo
            if (self.glue and self.glue.label == glue_label and
                self.glue.domain == self.domain):
                # Our glue record is valid. Don't go looking for a new one.
                pass
            else:
                # Ok, our glue record wasn't valid, let's find a new one.
                addr_glue = AddressRecord.objects.filter(label=glue_label,
                        domain=self.domain)
                intr_glue = StaticInterface.objects.filter(label=glue_label,
                        domain=self.domain)
                if not (addr_glue or intr_glue):
                    raise ValidationError(
                        "This NS needs a glue record. Create a glue "
                        "record for the server before creating "
                        "the NS record."
                    )
                else:
                    if addr_glue:
                        self.glue = addr_glue[0]
                    else:
                        self.glue = intr_glue[0]

    def check_NS_TLD_condition(ns):
        domain = Domain.objects.filter(name=ns.server)
        if not domain:
            return
        else:
            raise ValidationError("You cannot create a NS record that is the"
                                  "name of a domain.")

    def __repr__(self):
        return "<Forward '{0}'>".format(str(self))

    def __str__(self):
        return "{0} {1} {2}".format(self.domain.name, "NS", self.server)

    def _needs_glue(self):
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
