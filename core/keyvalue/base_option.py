from django.db import models
from django.core.exceptions import ValidationError

from mozdns.validation import validate_name
from core.keyvalue.models import KeyValue

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
        choices = ["unknown-clients", "bootp", "booting", "duplicates",
                   "declines", "client-updates", "dynamic bootp clients"]
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

            allow dynamic bootp clients;
            deny dynamic bootp clients;
        """

        choices = ["unknown-clients", "bootp", "booting", "duplicates",
                   "declines", "client-updates", "dynamic bootp clients"]
        self.is_statement = True
        self.is_option = False
        self.has_validator = True
        value = self._get_value()
        values = value.split(',')
        for value in values:
            if value.strip() in choices:
                continue
            else:
                raise ValidationError(
                    "Invalid parameter '{0}' for the option "
                    "'{1}'".format(self.value, self.key))

    def _routers(self, ip_type):
        """
        option routers ip-address [, ip-address... ];

            The routers option specifies a list of IP addresses for routers on
            the client's subnet. Routers should be listed in order of
            preference.
        """
        self.is_option = True
        self.is_statement = False
        self.has_validator = True
        self._ip_list(ip_type)

    def _ntp_servers(self, ip_type):
        """
        option ntp-servers ip-address [, ip-address... ];

            This option specifies a list of IP addresses indicating NTP (RFC
            1035) servers available to the client. Servers should be listed in
            order of preference.
        """
        self.is_option = True
        self.is_statement = False
        self.has_validator = True
        self._ip_list(ip_type)

    def _aa_domain_name_servers(self):
        """
        option domain-name-servers ip-address [, ip-address... ];

            The domain-name-servers option specifies a list of Domain Name
            System (STD 13, RFC 1035) name servers available to the client.
            Servers should be listed in order of preference.
        """
        self.is_option = True
        self.is_statement = False
        self.has_validator = True
        self._ip_list(self.obj.ip_type)

    def _aa_domain_name(self):
        """
        option domain-name text;

            The 'text' should be a space seperated domain names. I.E.:
            phx.mozilla.com phx1.mozilla.com This option specifies the domain
            name that client should use when resolving hostnames via the Domain
            Name System.
        """
        self.is_option = True
        self.is_statement = False
        self.has_validator = True
        value = self._get_value()
        for name in value.split(' '):
            validate_name(name)
        self.value = value

    def _aa_search_domain(self):
        """
        The domain-search option specifies a 'search list' of Domain Names to
        be used by the client to locate not-fully-qualified domain names. The
        difference between this option and historic use of the domain-name
        option for the same ends is that this option is encoded in RFC1035
        compressed labels on the wire. For example:

            option domain-search "example.com", "sales.example.com";
        """
        self.is_option = True
        self.is_statement = False
        self.has_validator = True
        value = self.value.strip(';')
        value = value.strip(' ')
        for name in value.split(','):
            # Bug here. Ex: "asf, "'asdf"'
            name = name.strip(' ')
            if not name:
                raise ValidationError("Each name needs to be a non empty "
                                      "domain name surrounded by \"\"")

            if name[0] != '"' and name[len(name) - 1] != '"':
                raise ValidationError("Each name needs to be a non empty "
                                      "domain name surrounded by \"\"")
            validate_name(name.strip('"'))

    def _ip_list(self, ip_type):
        """
        Use this if the value is supposed to be a list of ip addresses.
        """
        self.ip_option = True
        self.has_validator = True
        ips = self._get_value()
        ips = ips.split(',')
        for router in ips:
            router = router.strip()
            try:
                if ip_type == '4':
                    ipaddr.IPv4Address(router)
                else:
                    raise NotImplemented()
            except ipaddr.AddressValueError:
                raise ValidationError("Invalid option ({0}) parameter "
                                      "({1})'".format(self.key, router))

    def _single_ip(self, ip_type):
        ip = self._get_value()
        try:
            if ip_type == '4':
                ipaddr.IPv4Address(ip)
            else:
                raise NotImplemented()
        except ipaddr.AddressValueError:
            raise ValidationError("Invalid option ({0}) parameter "
                                  "({1})'".format(self.key, ip))
