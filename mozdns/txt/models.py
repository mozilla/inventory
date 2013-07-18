from string import Template

from django.db import models

from mozdns.models import MozdnsRecord, LabelDomainMixin
from mozdns.validation import validate_txt_data


import reversion


class TXT(MozdnsRecord, LabelDomainMixin):
    """
    >>> TXT(label=label, domain=domain, txt_data=txt_data)
    """

    id = models.AutoField(primary_key=True)
    txt_data = models.TextField(
        help_text="The text data for this record.",
        validators=[validate_txt_data]
    )

    search_fields = ("fqdn", "txt_data")

    template = ("{bind_name:$lhs_just} {ttl_} {rdclass:$rdclass_just} "
                "{rdtype:$rdtype_just} {txt_data:$rhs_just}")

    @classmethod
    def get_api_fields(cls):
        data = super(TXT, cls).get_api_fields() + ['txt_data']
        return data

    @property
    def rdtype(self):
        return 'TXT'

    def bind_render_record(self, pk=False):
        template = Template(self.template).substitute(**self.justs)
        bind_name = self.fqdn + "."

        txt_lines = self.txt_data.split('\n')
        if len(txt_lines) > 1:
            txt_data = '('
            for line in self.txt_data.split('\n'):
                txt_data += '"{0}"\n'.format(line)
            txt_data = txt_data.strip('\n') + ')'
        else:
            txt_data = '"{0}"'.format(self.txt_data)

        return template.format(
            bind_name=bind_name, ttl_='' if self.ttl is None else self.ttl,
            rdtype=self.rdtype, rdclass='IN', txt_data=txt_data
        )

    class Meta:
        db_table = "txt"
        # unique_together = ("domain", "label", "txt_data")
        # TODO
        # _mysql_exceptions.OperationalError: (1170, "BLOB/TEXT column
        # "txt_data" used in key specification without a key length")
        # Fix that ^

    def details(self):
        return (
            ("FQDN", self.fqdn),
            ("Record Type", "TXT"),
            ("Text", self.txt_data)
        )


reversion.register(TXT)
