from django.db import models
from django.core.exceptions import ValidationError


from mozdns.validation import validate_ip_type
from mozdns.ip.models import ipv6_to_longs
from core.utils import IPFilter, one_to_two, to_a
from core.vlan.models import Vlan
from core.site.models import Site
from core.mixins import ObjectUrlMixin, CoreDisplayMixin
from core.keyvalue.base_option import CommonOption, DHCPKeyValue
from core.keyvalue.mixins import KVUrlMixin
from truth.models import Truth

import ipaddr


class Network(models.Model, ObjectUrlMixin, CoreDisplayMixin, KVUrlMixin):
    id = models.AutoField(primary_key=True)
    vlan = models.ForeignKey(Vlan, null=True,
                             blank=True, on_delete=models.SET_NULL)
    site = models.ForeignKey(Site, null=True,
                             blank=True, on_delete=models.SET_NULL)

    # NETWORK/NETMASK FIELDS
    IP_TYPE_CHOICES = (('4', 'ipv4'), ('6', 'ipv6'))
    ip_type = models.CharField(max_length=1, choices=IP_TYPE_CHOICES,
                               editable=True, validators=[validate_ip_type])
    ip_upper = models.BigIntegerField(null=False, blank=True)
    ip_lower = models.BigIntegerField(null=False, blank=True)
    # This field is here so ES can search this model easier.
    network_str = models.CharField(max_length=49, editable=True,
                                   help_text="The network address of this "
                                   "network.")

    prefixlen = models.PositiveIntegerField(
        null=False, blank=True,
        help_text="The number of binary 1's in the netmask."
    )

    is_reserved = models.BooleanField(default=False, blank=False)

    dhcpd_raw_include = models.TextField(
        null=True, blank=True, help_text="The config options in this box "
        "will be included *as is* in the dhcpd.conf file for this "
        "subnet."
    )

    network = None

    template = (
        "{network_str:$lhs_just} {rdtype:$rdtype_just} IPv{ip_type:$rhs_just} "
        "vlan=:{vlan_str} site=:{site_str}"
    )

    class Meta:
        db_table = 'network'
        unique_together = ('ip_upper', 'ip_lower', 'prefixlen')

    def __str__(self):
        return "{0}".format(self.network_str)

    def __repr__(self):
        return "<Network {0}>".format(str(self))

    search_fields = ('network_str',)

    @classmethod
    def get_api_fields(cls):
        return ['network_str', 'prefixlen', 'ip_type', 'ip_upper', 'ip_lower']

    @property
    def rdtype(self):
        return 'NET'

    def bind_render_record(self, **kwargs):
        vlan_str = (
            '{0},{1}'.format(self.vlan.name, self.vlan.number)
            if self.vlan
            else 'None'
        )
        site_str = self.site.full_name if self.site else 'None'
        return super(Network, self).bind_render_record(
            vlan_str=vlan_str, site_str=site_str, **kwargs
        )

    def details(self):
        details = [
            ('Network', self.network_str),
            ('Reserved', self.is_reserved),
        ]
        if self.vlan:
            details.append(
                ('Vlan',
                 to_a("{0}:{1}".format(self.vlan.name, self.vlan.number),
                      self.vlan)))
        else:
            details.append(('Vlan', 'None'))

        if self.site:
            details.append(('Site', to_a(self.site.full_name, self.site)))
        else:
            details.append(('Site', 'None'))

        details.append((
            'DHCP Scope Name',
            self.calc_dhcp_scope_name() or 'No Valid Scope'
        ))

        return details

    def calc_dhcp_scope_name(self):
        """
        Introspect our vlan and site to see if we can calculate the DHCP scope
        name used to represent our "Truth Store". This is highly Mozilla
        specific.

        There are two ways in which a dhcp_scope can be found:
            1) Introspecting our keyvalue set for a dhcp_scope key
            2) Using a heuristic that uses the naming convention of dhcp_scope
                values and the site/vlan of this network
        The first method takes precedence over the second
        """
        try:
            return self.keyvalue_set.get(key='dhcp_scope').value
        except NetworkKeyValue.DoesNotExist:
            pass

        if self.vlan and self.site:
            # Grab the end of the full site name (usually the dc)
            scope_name = self.site.full_name.split('.')[-1]
            # If releng is in the site name, we need to add that to the scope
            if 'releng' in self.site.full_name:
                scope_name += '-releng'

            scope_name += "-vlan{0}".format(self.vlan.number)

            if Truth.objects.filter(name=scope_name).exists():
                return scope_name

        return None

    def delete(self, *args, **kwargs):
        if self.range_set.all().exists():
            raise ValidationError("Cannot delete this network because it has "
                                  "child ranges")
        super(Network, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.clean()
        super(Network, self).save(*args, **kwargs)

    def clean(self):
        self.update_network()
        # Look at all ranges that claim to be in this subnet, are they actually
        # in the subnet?
        for range_ in self.range_set.all():
            """
                I was writing checks to make sure that subnets wouldn't orphan
                ranges. IPv6 needs support.
            """
            fail = False
            # Check the start addresses.
            if range_.start_upper < self.ip_upper:
                fail = True
            elif (range_.start_upper > self.ip_upper and range_.start_lower <
                  self.ip_lower):
                fail = True
            elif (range_.start_upper == self.ip_upper and range_.start_lower
                  < self.ip_lower):
                fail = True

            if self.ip_type == '4':
                brdcst_upper, brdcst_lower = 0, int(self.network.broadcast)
            else:
                brdcst_upper, brdcst_lower = ipv6_to_longs(str(
                    self.network.broadcast))

            # Check the end addresses.
            if range_.end_upper > brdcst_upper:
                fail = True
            elif (range_.end_upper < brdcst_upper and range_.end_lower >
                  brdcst_lower):
                fail = True
            elif (range_.end_upper == brdcst_upper and range_.end_lower
                  > brdcst_lower):
                fail = True

            if fail:
                raise ValidationError("Resizing this subnet to the requested "
                                      "network prefix would orphan existing "
                                      "ranges.")

    def update_ipf(self):
        """Update the IP filter. Used for compiling search queries and firewall
        rules."""
        self.update_network()
        self.ipf = IPFilter(self.network.network, self.network.broadcast,
                            self.ip_type, object_=self)

    def update_network(self):
        """This function will look at the value of network_str to update other
        fields in the network object. This function will also set the 'network'
        attribute to either an ipaddr.IPv4Network or ipaddr.IPv6Network object.
        """
        if not isinstance(self.network_str, basestring):
            raise ValidationError("ERROR: No network str.")
        try:
            if self.ip_type == '4':
                self.network = ipaddr.IPv4Network(self.network_str)
            elif self.ip_type == '6':
                self.network = ipaddr.IPv6Network(self.network_str)
            else:
                raise ValidationError("Could not determine IP type of network"
                                      " %s" % (self.network_str))
        except (ipaddr.AddressValueError, ipaddr.NetmaskValueError):
            raise ValidationError("Invalid network for ip type of "
                                  "'{0}'.".format(self, self.ip_type))
        # Update fields
        self.ip_upper, self.ip_lower = one_to_two(int(self.network))
        self.prefixlen = self.network.prefixlen


class NetworkKeyValue(DHCPKeyValue, CommonOption):
    obj = models.ForeignKey(Network, related_name='keyvalue_set', null=False)
    aux_attrs = (
        ('description', 'A description of the site'),
    )

    class Meta:
        db_table = 'network_key_value'
        unique_together = ('key', 'value', 'obj')

    """The NetworkOption Class.

        "DHCP option statements always start with the option keyword, followed
        by an option name, followed by option data." -- The man page for
        dhcpd-options

        In this class, options are stored without the 'option' keyword. If it
        is an option, is option should be set.
    """

    def save(self, *args, **kwargs):
        self.clean()
        super(NetworkKeyValue, self).save(*args, **kwargs)

    def _aa_description(self):
        """
        A descrition of this network
        """
        pass

    def _aa_dhcp_scope(self):
        """
        The DHCP Scope associated with this network. Please reference
        https://inventory.mozilla.org/en-US/dhcp/show/ for a full list of valid
        DHCP Scopes.
        """
        if not Truth.objects.filter(name=self.value).exists():
            raise ValidationError(
                "The value {0} isn't a valid DHCP scope.".format(self.value)
            )

    def _aa_security_zone(self):
        """
        The security zone of this network.
        """
        pass

    def _aa_filename(self):
        """
        filename filename;

            The filename statement can be used to specify the name of the
            initial boot file which is to be loaded by a client. The filename
            should be a filename recognizable to whatever file transfer
            protocol the client can be expected to use to load the file.
        """
        self.is_statement = True
        self.is_option = False
        self.has_validator = True
        # Anything else?

    def _aa_next_server(self):
        """
        The next-server statement

            next-server server-name;

            The next-server statement is used to specify the host address
            of the server from which the initial boot file (specified in
            the filename statement) is to be loaded. Server-name should be
            a numeric IP address or a domain name. If no next-server
            parameter applies to a given client, the DHCP server's IP
            address is used.
        """
        self.has_validator = True
        self.is_statement = True
        self.is_option = False
        self._single_ip(self.obj.ip_type)

    def _aa_dns_servers(self):
        """
        A list of DNS servers for this network.
        """
        self.is_statement = False
        self.is_option = False
        self._ip_list(self.obj.ip_type)

    def _aa_routers(self):
        self._routers(self.obj.ip_type)

    def _aa_ntp_servers(self):
        self._ntp_servers(self.obj.ip_type)
