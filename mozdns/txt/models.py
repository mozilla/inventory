from gettext import gettext as _

from django.db import models

from mozdns.models import MozdnsRecord, LabelDomainMixin


import reversion


class TXT(MozdnsRecord, LabelDomainMixin):
    """
    >>> TXT(label=label, domain=domain, txt_data=txt_data)
    """

    id = models.AutoField(primary_key=True)
    txt_data = models.TextField(help_text="The text data for this record.")

    search_fields = ("fqdn", "txt_data")

    template = _("{bind_name:$lhs_just} {ttl} {rdclass:$rdclass_just} "
                 "{rdtype:$rdtype_just} \"{txt_data:$rhs_just}\"")

    def details(self):
        return (
            ("FQDN", self.fqdn),
            ("Record Type", "TXT"),
            ("Text", self.txt_data)
        )

    @classmethod
    def get_api_fields(cls):
        data = super(TXT, cls).get_api_fields() + ['txt_data']
        return data

    @property
    def rdtype(self):
        return 'TXT'

    class Meta:
        db_table = "txt"
        # unique_together = ("domain", "label", "txt_data")
        # TODO
        # _mysql_exceptions.OperationalError: (1170, "BLOB/TEXT column
        # "txt_data" used in key specification without a key length")
        # Fix that ^


reversion.register(TXT)
