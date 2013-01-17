from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models
from django.db.models import Q, F

from mozdns.validation import validate_name
from mozdns.mixins import ObjectUrlMixin, DisplayMixin
from mozdns.validation import validate_ttl

from settings import MOZDNS_BASE_URL
from core.keyvalue.models import KeyValue
from core.keyvalue.utils import AuxAttr

import reversion

from gettext import gettext as _
from string import Template
import time


# TODO, put these defaults in a config file.
ONE_WEEK = 604800
DEFAULT_EXPIRE = ONE_WEEK * 2
DEFAULT_RETRY = ONE_WEEK / 7  # One day
DEFAULT_REFRESH = 180  # 3 min
DEFAULT_MINIMUM = 180  # 3 min


class SOA(models.Model, ObjectUrlMixin, DisplayMixin):
    """
    SOA stands for Start of Authority

        "An SOA record is required in each *db.DOMAIN* and *db.ADDR* file."

        -- O'Reilly DNS and BIND

    The structure of an SOA::

        <name>  [<ttl>]  [<class>]  SOA  <origin>  <person>  (
                           <serial>
                           <refresh>
                           <retry>
                           <expire>
                           <minimum> )


        >>> SOA(primary=primary, contact=contact, retry=retry,
        ... refresh=refresh, description=description)

    Each DNS zone must have it's own SOA object. Use the description field to
    remind yourself which zone an SOA corresponds to if different SOA's have a
    similar ``primary`` and ``contact`` value.
    """

    id = models.AutoField(primary_key=True)
    ttl = models.PositiveIntegerField(default=3600, blank=True, null=True,
                                      validators=[validate_ttl],
                                      help_text="Time to Live of this record")
    primary = models.CharField(max_length=100, validators=[validate_name])
    contact = models.CharField(max_length=100, validators=[validate_name])
    serial = models.PositiveIntegerField(null=False, default=int(time.time()))
    # Indicates when the zone data is no longer authoritative. Used by slave.
    expire = models.PositiveIntegerField(null=False, default=DEFAULT_EXPIRE)
    # The time between retries if a slave fails to contact the master
    # when refresh (below) has expired.
    retry = models.PositiveIntegerField(null=False, default=DEFAULT_RETRY)
    # The time when the slave will try to refresh the zone from the master
    refresh = models.PositiveIntegerField(null=False, default=DEFAULT_REFRESH)
    minimum = models.PositiveIntegerField(null=False, default=DEFAULT_MINIMUM)
    description = models.CharField(max_length=200, null=True, blank=True)
    # This indicates if this SOA's zone needs to be rebuilt
    dirty = models.BooleanField(default=False)
    search_fields = ('primary', 'contact', 'description')
    template = _("{root_domain}. {ttl} {rdclass:$rdclass_just} "
                 "{rdtype:$rdtype_just} {primary}. {contact}. "
                 "({serial} {refresh} {retry} {expire})")

    attrs = None

    def bind_render_record(self):
        template = Template(self.template).substitute(**self.justs)
        return template.format(root_domain=self.root_domain,
                               rdtype=self.rdtype, rdclass='IN',
                               **self.__dict__)

    def update_attrs(self):
        self.attrs = AuxAttr(SOAKeyValue, self, 'soa')

    class Meta:
        db_table = 'soa'
        # We are using the description field here to stop the same SOA from
        # being assigned to multiple zones. See the documentation in the
        # Domain models.py file for more info.
        unique_together = ('primary', 'contact', 'description')

    def details(self):
        return (
            ('Primary', self.primary),
            ('Contact', self.contact),
            ('Serial', self.serial),
            ('Expire', self.expire),
            ('Retry', self.retry),
            ('Refresh', self.refresh),
            ('Description', self.description),
        )

    @property
    def rdtype(self):
        return 'SOA'

    @property
    def root_domain(self):
        try:
            return self.domain_set.get(~Q(master_domain__soa=F('soa')),
                                       soa__isnull=False)
        except ObjectDoesNotExist:
            return None

    def get_debug_build_url(self):
        return MOZDNS_BASE_URL + "/bind/build_debug/{0}/".format(self.pk)

    def delete(self, *args, **kwargs):
        if self.domain_set.exists():
            raise ValidationError(
                "Domains exist in this SOA's zone. Delete "
                "those domains or remove them from this zone before "
                "deleting this SOA.")
        super(SOA, self).delete(*args, **kwargs)

    def has_record_set(self, exclude_ns=False):
        for domain in self.domain_set.all():
            if domain.has_record_set(exclude_ns=exclude_ns):
                return True
        return False

    def save(self, *args, **kwargs):
        # Look a the value of this object in the db. Did anything change? If
        # yes, mark yourself as 'dirty'.
        self.full_clean()
        if self.pk:
            db_self = SOA.objects.get(pk=self.pk)
            fields = ['primary', 'contact', 'expire', 'retry',
                      'refresh', 'description']
            # Leave out serial for obvious reasons
            for field in fields:
                if getattr(db_self, field) != getattr(self, field):
                    self.dirty = True
        else:  # No pk means we are a new object
            self.dirty = True
        super(SOA, self).save(*args, **kwargs)

    def __str__(self):
        return "{0}".format(str(self.description))

    def __repr__(self):
        return "<'{0}'>".format(str(self))


reversion.register(SOA)


class SOAKeyValue(KeyValue):
    soa = models.ForeignKey(SOA, null=False)

    def _aa_disabled(self):
        """
        Disabled - The Value of this Key determines whether or not an SOA will
        be asked to build a zone file. Values that represent true are 'True,
        TRUE, true, 1' and 'yes'. Values that represent false are 'False,
        FALSE, false, 0' and 'no'.
        """
        true_values = ["true", "1", "yes"]
        false_values = ["false", "0", "no"]
        if self.value.lower() in true_values:
            self.value = "True"
        elif self.value.lower() in false_values:
            self.value = "False"
        else:
            raise ValidationError("Disabled should be set to either {0} OR "
                                  "{1}".format(", ".join(true_values),
                                               ", ".join(false_values)))


reversion.register(SOAKeyValue)
