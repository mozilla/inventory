from django.db import models
from django.core.exceptions import ValidationError

from mozdns.models import MozdnsRecord
from mozdns.cname.models import CNAME

from mozdns.validation import validate_mx_priority
from mozdns.validation import validate_name

import reversion

from gettext import gettext as _

class MX(MozdnsRecord):
    """
    >>> MX(label=label, domain=domain, server=server, priority=prio,
    ...     ttl=tll)
    """
    id = models.AutoField(primary_key=True)
    # The mail server this record should point to.
    server = models.CharField(max_length=100, validators=[validate_name],
                help_text="The name of the mail server this record points to.")
    priority = models.PositiveIntegerField(null=False,
                        validators=[validate_mx_priority])
    template = _("{bind_name:$lhs_just} {ttl} {rdclass:$rdclass_just} "
                 "{rdtype:$rdtype_just}{priority:$prio_just} "
                 "{server:$rhs_just}.")
    search_fields = ('fqdn', 'server')


    def details(self):
        return  (
                    ('FQDN', self.fqdn),
                    ('Record Type', 'MX'),
                    ('Server', self.server),
                    ('Priority', self.priority),
                    ('TTL', self.ttl)
                )

    class Meta:
        db_table = 'mx'
        unique_together = ('domain', 'label', 'server', 'priority')

    @property
    def rdtype(self):
        return 'MX'

    def __str__(self):
        return "{0} {1} {3} {4} {5}".format(self.fqdn, self.ttl, 'IN', 'MX',
                                            self.priority, self.server)

    def __repr__(self):
        return "<MX '{0}'>".format(str(self))


    @classmethod
    def get_api_fields(cls):
        return super(MX, cls).get_api_fields() + ['server', 'priority']

    def save(self, *args, **kwargs):
        self.full_clean()
        super(MX, self).save(*args, **kwargs)

    def clean(self, *args, **kwargs):
        super(MX, self).clean(*args, **kwargs)
        super(MX, self).check_for_delegation()
        super(MX, self).check_for_cname()
        self.no_point_to_cname()

    def no_point_to_cname(self):
        """MX records should not point to CNAMES."""
        # TODO, cite an RFC.
        if CNAME.objects.filter(fqdn=self.server):
            raise ValidationError("MX records should not point to CNAMES.")

reversion.register(MX)
