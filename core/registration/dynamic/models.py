from django.db import models

from core.ctnr.models import Ctnr
from core.registration.models import BaseRegistration
from mozdns.mozdhcp.range.models import Range


class DynamicRegistration(BaseRegistration):
    Ctnr = models.ForeignKey(Ctnr, null=False)
    range = models.ForeignKey(Range, null=False)

    class Meta:
        db_table = 'dynamic_registration'
