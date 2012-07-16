import time

from django.db import models

from mozdns.validation import validate_name
from mozdns.mixins import ObjectUrlMixin


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

    An SOA instance can be created using the SOA class constructure::

        >>> SOA(primary=primary, contact=contact, retry=retry,
        ... refresh=refresh, comment=comment)

    Each DNS zone must have it's own SOA object. Use the comment field
    to remind yourself of which zone an SOA corresponds to if a zone has
    similar ``primary`` and ``contact`` values.
    """

    id = models.AutoField(primary_key=True)
    primary = models.CharField(max_length=100, validators=[validate_name])
    contact = models.CharField(max_length=100, validators=[validate_name])
    serial = models.PositiveIntegerField(null=False)
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

    def delete(self, *args, **kwargs):
        super(SOA, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.serial = int(time.time())
        self.full_clean()
        self.dirty = True
        super(SOA, self).save(*args, **kwargs)

    def __str__(self):
        return "{0}".format(str(self.comment))

    def __repr__(self):
        return "<'{0}'>".format(str(self))
