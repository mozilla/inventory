from django.core.exceptions import ValidationError

from mozdns.validation import validate_name


class KVUrlMixin(object):
    def get_kv_url(self):
        return '/en-US/core/keyvalue/{0}/{1}/'.format(
            self.keyvalue_set.model.__name__.lower(), self.pk
        )


class HWAdapterMixin(object):
    # Make sure you mix this in with a class that inherits from DHCPKeyValue
    def _aa_host_name(self):
        """
        option host-name text;

            This option specifies the name of the client. The name may or may
            not be qualified with the local domain name (it is preferable to
            use the domain-name option to specify the domain name). See RFC
            1035 for character set restrictions. This option is only honored by
            dhclient-script(8) if the hostname for the client machine is not
            set.
        """
        self.is_option = True
        self.is_statement = False
        self.has_validator = True
        if not (self.value.startswith('"') and self.value.endswith('"')):
            self.value = '"' + self.value + '"'
        validate_name(self.value.strip('"'))

    def _aa_domain_name_servers(self):
        """
        DHCP option domain-name-servers
        """
        if not self.value:
            raise ValidationError("Domain Name Servers Required")

    def _aa_domain_name(self):
        """
        DHCP option domain-name
        """
        if not self.value:
            raise ValidationError("Domain Name Required")

    def _aa_filename(self):
        """
        DHCP option filename
        """
        if not self.value:
            raise ValidationError("Filename Required")
