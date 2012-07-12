from django.db import models
from django.core.exceptions import ValidationError

from mozdns.validation import validate_name
from core.keyvalue.models import KeyValue

import pdb
import ipaddr

class CommonOption(KeyValue):
    is_option = models.BooleanField(default=False)
    is_statement = models.BooleanField(default=False)
    has_validator = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def _get_value(self):
        value = self.value.strip('\'" ')
        value = value.strip(';')
        value = value.strip()
        return value

    def _aa_deny(self):
        """
        See allow.
        """
        choices = ["unknown-clients", "bootp", "booting", "duplicates", "declines", "client-updates"]
        self.is_statement = True
        self.is_option = False
        self.has_validator = True
        value = self._get_value()
        values = value.split(',')
        for value in values:
            if value in choices:
                continue
            else:
                raise ValidationError("Invalid option ({0}) parameter "
                    "({1})'".format(self.key, self.value))

    def _aa_allow(self):
        """
        The following usages of allow and deny will work in any scope, although
        it is not recommended that they be used in pool declarations.

            allow unknown-clients;
            deny unknown-clients;
            ignore unknown-clients;

            allow bootp;
            deny bootp;
            ignore bootp;
            allow booting;
            deny booting;
            ignore booting;

            allow duplicates;
            deny duplicates;

            allow declines;
            deny declines;
            ignore declines;

            allow client-updates;
            deny client-updates;
        """

        choices = ["unknown-clients", "bootp", "booting", "duplicates", "declines", "client-updates"]
        self.is_statement = True
        self.is_option = False
        self.has_validator = True
        value = self._get_value()
        values = value.split(',')
        for value in values:
            if value.strip() in choices:
                continue
            else:
                raise ValidationError("Invalid option ({0}) parameter "
                    "({1})'".format(self.key, self.value))

    def _aa_routers(self):
        """
        option routers ip-address [, ip-address... ];

            The routers option specifies a list of IP addresses for routers on
            the client's subnet. Routers should be listed in order of
            preference.
        """
        self.is_option = True
        self.is_statement = False
        self.has_validator = True
        self._ip_list()

    def _aa_ntp_servers(self):
        """
        option ntp-servers ip-address [, ip-address... ];

            This option specifies a list of IP addresses indicating NTP (RFC
            1035) servers available to the client. Servers should be listed in
            order of preference.
        """
        self.is_option = True
        self.is_statement = False
        self.has_validator = True
        self._ip_list()

    def _aa_domain_name_servers(self):
        """
        option domain-name-servers ip-address [, ip-address... ];

            The domain-name-servers option specifies a list of Domain Name System (STD
            13, RFC 1035) name servers available to the client. Servers should be listed in
            order of preference.
        """
        self.is_option = True
        self.is_statement = False
        self.has_validator = True
        self._ip_list()

    def _aa_domain_name(self):
        """See domain name servers."""
        self.is_option = True
        self.is_statement = False
        self.has_validator = True
        value = self._get_value()
        validate_name(value)


