from django.db import models

from mozdns.domain.models import Domain
from mozdns.models import MozdnsRecord

from mozdns.validation import validate_srv_label, validate_srv_port
from mozdns.validation import validate_srv_priority, validate_srv_weight
from mozdns.validation import validate_srv_name
from mozdns.validation import validate_srv_target

import reversion

from gettext import gettext as _


class SRV(MozdnsRecord):
    """
    >>> SRV(label=label, domain=domain, target=target, port=port,
    ... priority=priority, weight=weight, ttl=ttl)
    """
    id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=63, blank=True, null=True,
                             validators=[validate_srv_label],
                             help_text="Short name of the fqdn")
    domain = models.ForeignKey(Domain, null=False, help_text="FQDN of the "
                               "domain after the short hostname. "
                               "(Ex: <i>Vlan</i>.<i>DC</i>.mozilla.com)")
    fqdn = models.CharField(max_length=255, blank=True, null=True,
                            validators=[validate_srv_name])
    # fqdn = label + domain.name <--- see set_fqdn

    target = models.CharField(max_length=100,
                              validators=[validate_srv_target], blank=True,
                              null=True)

    port = models.PositiveIntegerField(null=False,
                                       validators=[validate_srv_port])

    priority = models.PositiveIntegerField(null=False,
                                           validators=[validate_srv_priority])

    weight = models.PositiveIntegerField(null=False,
                                         validators=[validate_srv_weight])

    template = _("{bind_name:$lhs_just} {ttl} {rdclass:$rdclass_just} "
                 "{rdtype:$rdtype_just} {priority:$prio_just} "
                 "{weight:$extra_just} {port:$extra_just} "
                 "{target:$extra_just}.")

    search_fields = ("fqdn", "target")

    def details(self):
        return (
            ("FQDN", self.fqdn),
            ("Record Type", "SRV"),
            ("Targer", self.target),
            ("Port", self.port),
            ("Priority", self.priority),
            ("Weight", self.weight),
        )

    class Meta:
        db_table = "srv"
        unique_together = ("label", "domain", "target", "port")

    @classmethod
    def get_api_fields(cls):
        return super(SRV, cls).get_api_fields() + [
            'port', 'weight', 'priority', 'target']

    @property
    def rdtype(self):
        return 'SRV'


reversion.register(SRV)
