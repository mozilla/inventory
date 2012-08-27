from django.db import models
from django.core.exceptions import ValidationError

from mozdns.models import MozdnsRecord


def validate_algorithm(number):
    if number not in ('1','2'):
        raise ValidationError("Algorithm number must be with 1 (RSA) or 2 (DSA)")

def validate_fingerprint(number):
    if number not in ('1',):
        raise ValidationError("Fingerprint type must be 1 (SHA-1)")

class SSHFP(MozdnsRecord):
    """
    >>> SSHFP(label=label, domain=domain, key=key_data,
    ... algorithm_number=algo_num, fingerprint_type=fing_type)
    """

    id = models.AutoField(primary_key=True)
    key = models.TextField()
    algorithm_number = models.PositiveIntegerField(null=False, blank=False,
            validators=[validate_algorithm], help_text="Algorithm number must "
            "be with 1 (RSA) or 2 (DSA)")
    fingerprint_type = models.PositiveIntegerField(null=False, blank=False,
            validators=[validate_fingerprint], help_text="Fingerprint type "
            "must be 1 (SHA-1)")

    search_feilds = ("fqdn", "key")

    def details(self):
        return (
                ("FQDN", self.fqdn),
                ("Record Type", "SSHFP"),
                ("Algorithm", self.algorithm_number),
                ("Finger Print Type", self.fingerprint_type),
                ("Key", self.key),
               )

    def save(self, *args, **kwargs):
        super(SSHFP, self).save(*args, **kwargs)

    def clean(self):
        super(SSHFP, self).clean()
        super(SSHFP, self).check_for_delegation()
        super(SSHFP, self).check_for_cname()

    class Meta:
        db_table = "sshfp"
        # unique_together = ('domain', 'label', 'txt_data')
        # TODO
        # _mysql_exceptions.OperationalError: (1170, "BLOB/TEXT column
        # 'txt_data' used in key specification without a key length")
        # Fix that ^
