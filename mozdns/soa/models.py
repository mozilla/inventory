import time
from django.core.exceptions import ValidationError

from django.db import models

from mozdns.validation import validate_name
from mozdns.mixins import ObjectUrlMixin

from settings import MOZDNS_BASE_URL
from core.keyvalue.models import KeyValue
from core.keyvalue.utils import AuxAttr
import os


#TODO, put these defaults in a config file.
ONE_WEEK = 604800
DEFAULT_EXPIRE = ONE_WEEK * 2
DEFAULT_RETRY = ONE_WEEK / 7  # One day
DEFAULT_REFRESH = 180  # 3 min
DEFAULT_MINIMUM = 180  # 3 min


class SOA(models.Model, ObjectUrlMixin):
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
        ... refresh=refresh, comment=comment)

    Each DNS zone must have it's own SOA object. Use the comment field to
    remind yourself which zone an SOA corresponds to if different SOA's have a
    similar ``primary`` and ``contact`` value.
    """

    id = models.AutoField(primary_key=True)
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
    comment = models.CharField(max_length=200, null=True, blank=True)
    # This indicates if this SOA needs to be rebuilt
    dirty = models.BooleanField(default=False)

    search_fields = ('primary', 'contact', 'comment')

    attrs = None

    def update_attrs(self):
        self.attrs = AuxAttr(SOAKeyValue, self, 'soa')

    class Meta:
        db_table = 'soa'
        # We are using the comment field here to stop the same SOA from
        # being assigned to multiple zones. See the documentation in the
        # Domain models.py file for more info.
        unique_together = ('primary', 'contact', 'comment')

    def details(self):
        return  (
                    ('Primary', self.primary),
                    ('Contact', self.contact),
                    ('Serial', self.serial),
                    ('Expire', self.expire),
                    ('Retry', self.retry),
                    ('Refresh', self.refresh),
                    ('Comment', self.comment),
                )

    def get_debug_build_url(self):
        return MOZDNS_BASE_URL + "/bind/build_debug/{0}/".format(self.pk)

    def delete(self, *args, **kwargs):
        super(SOA, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        # Look a the value of this object in the db. Did anything change? If
        # yes, mark yourself as 'dirty'.
        self.full_clean()
        if self.pk:
            db_self = SOA.objects.get(pk=self.pk)
            fields = ['primary', 'contact', 'serial', 'expire', 'retry',
                    'refresh', 'comment']
            for field in fields:
                if getattr(db_self, field) != getattr(self, field):
                    self.dirty = True
        super(SOA, self).save(*args, **kwargs)

    def __str__(self):
        return "{0}".format(str(self.comment))

    def __repr__(self):
        return "<'{0}'>".format(str(self))

class SOAKeyValue(KeyValue):
    soa = models.ForeignKey(SOA, null=False)

    def _aa_dir_path(self):
        """Filepath - Where should the build scripts put the zone file for this
        zone?"""
        if not os.access(self.value, os.R_OK):
            raise ValidationError("Couldn't find {0} on the system running "
                    "this code. Please create this path.".format(self.value))

    def _aa_disabled(self):
        """Disabled - The Value of this Key determines whether or not an SOA will
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
