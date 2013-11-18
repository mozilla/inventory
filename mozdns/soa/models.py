from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models
from django.db.models import Q, F

from mozdns.mixins import ObjectUrlMixin, DisplayMixin
from mozdns.validation import validate_ttl, validate_soa_serial, validate_name

from settings import MOZDNS_BASE_URL
from core.keyvalue.models import KeyValue
from core.keyvalue.utils import AuxAttr

from core.task.models import Task

import reversion

from gettext import gettext as _
from string import Template
import datetime


# TODO, put these defaults in a config file.
ONE_WEEK = 604800
DEFAULT_EXPIRE = ONE_WEEK * 2
DEFAULT_RETRY = 3 * 60  # 3 min
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


        >>> SOA(primary=primary, contact=contact, retry=retry,  # noqa
        ... refresh=refresh, description=description)  # noqa

    Each DNS zone must have it's own SOA object. Use the description field to
    remind yourself which zone an SOA corresponds to if different SOA's have a
    similar ``primary`` and ``contact`` value.
    """

    id = models.AutoField(primary_key=True)
    ttl = models.PositiveIntegerField(
        default=3600, blank=True, null=True, validators=[validate_ttl],
        help_text='Time to Live of this record'
    )
    primary = models.CharField(max_length=100, validators=[validate_name])
    contact = models.CharField(max_length=100, validators=[validate_name])
    serial = models.PositiveIntegerField(
        null=False, default=int(datetime.datetime.now().strftime('%Y%m%d01')),
        validators=[validate_soa_serial]
    )
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
    is_signed = models.BooleanField(default=False)
    search_fields = ('description',)
    template = _("{root_domain}. {ttl_} {rdclass:$rdclass_just} "
                 "{rdtype:$rdtype_just} {primary}. {contact}. "
                 "({serial} {refresh} {retry} {expire})")

    attrs = None

    class Meta:
        db_table = 'soa'
        # We are using the description field here to stop the same SOA from
        # being assigned to multiple zones. See the documentation in the
        # Domain models.py file for more info.
        unique_together = ('primary', 'contact', 'description')

    @classmethod
    def calc_serial(cls, cur_serial, date):
        """
            "The convention is to use a date based sn (serial) value to
            simplify the task of incrementing the sn - the most popular
            convention being yyyymmddss where yyyy = year, mm = month and dd =
            day ss = a sequence number in case you update it more than once in
            the day!  Using this date format convention the value 2005021002
            indicates the last update was on the 10th February 2005 and it was
            the third update that day. The date format is just a convention,
            not a requirement, so BIND (or any other DNS software) will not
            validate the contents of this field."
                -- http://www.zytrax.com/books/dns/ch8/soa.html

        Calculate the correct serial given that today is YYYYMMDD and the
        current serial is a 10 digit number.

        Cases:
            cur_serial isn't a date -> +1 serial. Never go backwards.
            cur_serial > date -> +1 serial. Never go backwards.
            cur_serial == date -> +1 serial
            cur_serial < date -> now_date_stamp + '00'

        Everything comes in as string and leaves as an int

        :param date: A date
        :type date: datetime.date object
        :param cur_serial: The current 10 digit serial number
        :type cur_serial: str
        """

        date_serial = int(date.strftime('%Y%m%d00'))
        if int(cur_serial) < date_serial:
            return date_serial
        else:
            return int(cur_serial) + 1

    @property
    def rdtype(self):
        return 'SOA'

    @property
    def root_domain(self):
        try:
            return self.domain_set.get(
                ~Q(master_domain__soa=F('soa')), soa__isnull=False
            )
        except ObjectDoesNotExist:
            return None

    def get_incremented_serial(self):
        return self.__class__.calc_serial(
            str(self.serial), datetime.date.today()
        )

    def bind_render_record(self, show_ttl=False):
        template = Template(self.template).substitute(**self.justs)
        if show_ttl:
            ttl_ = self.ttl
        else:
            ttl_ = '' if self.ttl is None else self.ttl
        return template.format(
            root_domain=self.root_domain, rdtype=self.rdtype, rdclass='IN',
            ttl_=ttl_, **vars(self)
        )

    def update_attrs(self):
        self.attrs = AuxAttr(SOAKeyValue, self, 'soa')

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

    def get_debug_build_url(self):
        return MOZDNS_BASE_URL + '/bind/build_debug/{0}/'.format(self.pk)

    def get_fancy_edit_url(self):
        return '/mozdns/soa/{0}/update'.format(self.pk)

    def delete(self, *args, **kwargs):
        if self.domain_set.exists():
            raise ValidationError(
                "Domains exist in this SOA's zone. Delete "
                "those domains or remove them from this zone before "
                "deleting this SOA.")
        Task.schedule_all_dns_rebuild(self)
        super(SOA, self).delete(*args, **kwargs)

    def has_record_set(self, view=None, exclude_ns=False):
        for domain in self.domain_set.all():
            if domain.has_record_set(view=view, exclude_ns=exclude_ns):
                return True
        return False

    def schedule_rebuild(self, commit=True):
        Task.schedule_zone_rebuild(self)
        self.dirty = True
        if commit:
            self.save()

    def schedule_full_rebuild(self, commit=True):
        Task.schedule_all_dns_rebuild(self)
        self.dirty = True
        if commit:
            self.save()

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.pk:
            new = True
            self.dirty = True
        elif self.dirty:
            new = False
        else:
            new = False
            db_self = SOA.objects.get(pk=self.pk)
            fields = [field.name for field in self.__class__._meta.fields]
            # Introspec and determine if we need to rebuild
            for field in fields:
                # Leave out serial and dirty so rebuilds don't cause a never
                # ending build cycle
                if field in ('serial', 'dirty'):
                    continue
                if getattr(db_self, field) != getattr(self, field):
                    self.schedule_rebuild(commit=False)

        super(SOA, self).save(*args, **kwargs)

        if new:
            # Need to call this after save because new objects won't have a pk
            self.schedule_full_rebuild(commit=False)

    def __str__(self):
        return self.description

    def __repr__(self):
        return "<SOA '{0}'>".format(self)


reversion.register(SOA)


class SOAKeyValue(KeyValue):
    obj = models.ForeignKey(SOA, related_name='keyvalue_set', null=False)

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
