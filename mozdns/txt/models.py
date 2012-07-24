from django.db import models

from mozdns.models import MozdnsRecord


class TXT(MozdnsRecord):
    """
    >>> TXT(label=label, domain=domain, txt_data=txt_data)
    """

    id = models.AutoField(primary_key=True)
    txt_data = models.TextField()

    search_feilds = ('fqdn', 'txt_data')

    def details(self):
        return (
                ('FQDN', self.fqdn),
                ('Record Type', 'TXT'),
                ('Text', self.txt_data)
               )

    def save(self, *args, **kwargs):
        self.full_clean()
        super(TXT, self).save(*args, **kwargs)

    def clean(self):
        super(TXT, self).clean()
        super(TXT, self).check_for_delegation()
        super(TXT, self).check_for_cname()

    class Meta:
        db_table = 'txt'
        # unique_together = ('domain', 'label', 'txt_data')
        # TODO
        # _mysql_exceptions.OperationalError: (1170, "BLOB/TEXT column
        # 'txt_data' used in key specification without a key length")
        # Fix that ^
