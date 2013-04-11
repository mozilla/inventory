from django.db import models
from django.core.exceptions import ValidationError

from mozdns.models import MozdnsRecord, LabelDomainMixin

import reversion

from gettext import gettext as _
import re


def validate_algorithm(number):
    if number not in (1, 2):
        raise ValidationError(
            "Algorithm number must be with 1 (RSA) or 2 (DSA)")


def validate_fingerprint(number):
    if number not in (1,):
        raise ValidationError("Fingerprint type must be 1 (SHA-1)")


is_sha1 = re.compile("[0-9a-fA-F]{40}")


def validate_sha1(sha1):
    if not is_sha1.match(sha1):
        raise ValidationError("Invalid key.")


class SSHFP(MozdnsRecord, LabelDomainMixin):
    """
    >>> SSHFP(label=label, domain=domain, key=key_data,
    ... algorithm_number=algo_num, fingerprint_type=fing_type)
    """

    id = models.AutoField(primary_key=True)
    key = models.CharField(max_length=256, validators=[validate_sha1])
    algorithm_number = models.PositiveIntegerField(
        null=False, blank=False, validators=[validate_algorithm],
        help_text="Algorithm number must be with 1 (RSA) or 2 (DSA)")
    fingerprint_type = models.PositiveIntegerField(
        null=False, blank=False, validators=[validate_fingerprint],
        help_text="Fingerprint type must be 1 (SHA-1)")

    template = _("{bind_name:$lhs_just} {ttl} {rdclass:$rdclass_just} "
                 "{rdtype:$rdtype_just} {algorithm_number} {fingerprint_type} "
                 "{key:$rhs_just}")

    search_fields = ("fqdn", "key")

    def details(self):
        return (
            ("FQDN", self.fqdn),
            ("Record Type", "SSHFP"),
            ("Algorithm", self.algorithm_number),
            ("Finger Print Type", self.fingerprint_type),
            ("Key", self.key),
        )

    @classmethod
    def get_api_fields(cls):
        return super(SSHFP, cls).get_api_fields() + ['fingerprint_type',
                                                     'algorithm_number', 'key']

    @property
    def rdtype(self):
        return 'SSHFP'

    class Meta:
        db_table = "sshfp"
        # unique_together = ('domain', 'label', 'txt_data')
        # TODO
        # _mysql_exceptions.OperationalError: (1170, "BLOB/TEXT column
        # 'txt_data' used in key specification without a key length")
        # Fix that ^


reversion.register(SSHFP)
