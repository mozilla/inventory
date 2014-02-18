from django.db import models

from systems.models import System
from slurpee.constants import (
    P_OVERLAY, P_OVERWRITE, P_EXTRA, P_MANAGED,
    RAW_TEXT, JSON_TEXT
)


class ExternalData(models.Model):
    # ExternalData.name is what Inventory references the data as.
    # For example: puppet calls a serial 'serialnumber' but Inventory calls
    # it 'serial'. In that case ExternalData.name would be 'serial' and
    # ExternalData.source_name would be 'serialnumber'

    # If ExternalData.policy is default (its just extra data) we set
    # ExternalData.name to ExternalData.source_name
    system = models.ForeignKey(System, null=False)
    name = models.CharField(max_length=255, null=False)
    data = models.CharField(max_length=1023, null=False)
    source = models.CharField(max_length=255, null=False)
    source_name = models.CharField(max_length=255, null=False)
    atime = models.DateTimeField(auto_now=True, auto_now_add=True)

    DATA_TYPES = (
        (RAW_TEXT, 'Raw Text'),
        (JSON_TEXT, 'JSON Text'),
    )

    dtype = models.CharField(
        max_length=2, choices=DATA_TYPES, default=RAW_TEXT
    )

    POLICY_TYPE = (
        (P_OVERLAY, 'overlay'),
        (P_OVERWRITE, 'overwrite'),
        (P_EXTRA, 'extra'),
        (P_MANAGED, 'managed')
    )

    policy = models.CharField(
        max_length=2, choices=POLICY_TYPE, default=P_EXTRA
    )

    def __str__(self):
        return "{0} ({1}): {2}".format(self.name, self.policy, self.data)
