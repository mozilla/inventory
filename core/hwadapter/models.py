from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError

from core.group.models import Group
from core.keyvalue.base_option import DHCPKeyValue, CommonOption
from core.keyvalue.mixins import KVUrlMixin, HWAdapterMixin
from core.mixins import ObjectUrlMixin
from core.registration.static.models import StaticReg
from core.validation import validate_mac, validate_hw_name
from core.utils import create_key_index

from truth.models import Truth

import reversion


class HWAdapter(models.Model, ObjectUrlMixin, KVUrlMixin):
    id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    enable_dhcp = models.BooleanField(blank=False, null=False, default=True)
    name = models.CharField(
        max_length=255, null=False, validators=[validate_hw_name],
        blank=True, help_text="(Leave blank and Inventory will choose for you)"
    )
    mac = models.CharField(
        max_length=17, validators=[validate_mac],
        help_text="Mac address in format XX:XX:XX:XX:XX:XX"
    )
    group = models.ForeignKey(Group, null=True, blank=True)
    sreg = models.ForeignKey(
        StaticReg, null=True, blank=True, related_name='hwadapter_set'
    )

    search_fields = ('mac', 'group__name', 'sreg__ip_str', 'sreg__fqdn')

    class Meta:
        db_table = 'hwadapter'
        unique_together = (
            ('mac', 'sreg'),
            ('sreg', 'name')
        )

    def __str__(self):
        return '{0}'.format(self.mac)

    def __repr__(self):
        return '<HWAdapter: {0}>'.format(self)

    @classmethod
    def get_api_fields(cls):
        return ['mac', 'name', 'description', 'enable_dhcp']

    @classmethod
    def get_bulk_action_list(cls, query, fields=None):
        if not fields:
            fields = cls.get_api_fields() + ['pk', 'sreg']

        hw_t_bundles = cls.objects.filter(query).values_list(*fields)

        d_bundles = {}
        for t_bundle in hw_t_bundles:
            d_bundle = dict(zip(fields, t_bundle))
            d_bundle['keyvalue_set'] = create_key_index(
                cls.keyvalue_set.related.model.objects.filter(
                    obj=d_bundle['pk']
                ).values('key', 'value', 'pk')
            )
            sreg = d_bundle.pop('sreg')
            d_bundles.setdefault(sreg, {})[d_bundle['name']] = d_bundle

        return d_bundles

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.sreg:
            raise ValidationError(
                "Hardware Adapters need to be associated with a static IP "
                "registration"
            )

        if not self.name:
            self.name = self.calc_name()

        if self.sreg.hwadapter_set.filter(~Q(pk=self.pk), name=self.name):
            raise ValidationError("A hwadapter already has this name")
        super(HWAdapter, self).save(*args, **kwargs)

    def calc_name(self):
        """
        Find a suitable name for a hwadapter if the user did not set one.
        """
        if not self.sreg:
            return  # Someone else will notice this
        if self.pk:
            hws = self.sreg.hwadatper_set.filter(~Q(pk=self.pk))
        else:
            hws = self.sreg.hwadapter_set.all()

        if not hws.exists():
            return 'hw0'

        num = 0
        name = ''
        # Guess and check.
        while True:
            tmp_name = 'hw{num}'.format(num=num)
            if not hws.filter(name=tmp_name).exists():
                name = tmp_name
                break
            else:
                num += 1

        return name

    def get_absolute_url(self):
        return self.sreg.system.get_absolute_url()


class HWAdapterKeyValue(HWAdapterMixin, DHCPKeyValue, CommonOption):
    obj = models.ForeignKey(
        HWAdapter, related_name='keyvalue_set', null=False
    )

    class Meta:
        db_table = 'hwadapter_key_value'
        unique_together = ('key', 'obj')

    def _aa_dhcp_scope(self):
        """
        A Valid DHCP scope. Find them here:
        https://inventory.mozilla.org/en-US/dhcp/show/
        """
        if not Truth.objects.filter(name=self.value).exists():
            raise ValidationError(
                "The value {0} isn't a valid DHCP scope.".format(self.value)
            )

reversion.register(HWAdapter)
