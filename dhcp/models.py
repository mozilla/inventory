from django.db import models

class DHCPOverride(models.Model):

    dhcp_scope = models.CharField(max_length=32)
    override_text = models.TextField(blank=True, null=True)
    class Meta:
        db_table = u'dhcp_overrides'

class DHCPFile(models.Model):

    dhcp_scope = models.CharField(max_length=32)
    file_text = models.TextField(blank=True, null=True)
    class Meta:
        db_table = u'dhcp_file'

class DHCP(models.Model):
    SUBNET_CHOICES = (
        ('255.255.254.0', '255.255.254.0'),
        ('255.255.255.0', '255.255.255.0'),
        ('255.255.255.128', '255.255.255.128'),
        ('255.255.255.192', '255.255.255.192'),
        ('255.255.255.224', '255.255.255.224'),
        ('255.255.255.240', '255.255.255.240'),
        ('255.255.255.248', '255.255.255.248'),
        ('255.255.255.252', '255.255.255.252'),
        ('255.255.255.254', '255.255.255.254')
    )

    YES_NO_CHOICES = (
    (0, 'No'),
    (1, 'Yes'),
    )

    scope_name = models.CharField(max_length=64)
    scope_start = models.CharField(max_length=16, blank=True, null=True)
    scope_netmask = models.CharField(max_length=32, choices=SUBNET_CHOICES)
    scope_notes = models.TextField(max_length=512, blank=True, null=True)
    filename = models.CharField(max_length=32, blank=True, null=True)
    pool_range_start = models.CharField(max_length=16, blank=True, null=True)
    pool_range_end = models.CharField(max_length=16, blank=True, null=True)
    pool_deny_dynamic_bootp_agents = models.IntegerField(max_length=32, choices=YES_NO_CHOICES)
    allow_booting = models.IntegerField(max_length=32, choices=YES_NO_CHOICES)
    allow_bootp = models.IntegerField(max_length=32, choices=YES_NO_CHOICES)
    option_ntp_servers = models.CharField(max_length=32, blank=True, null=True)
    option_subnet_mask = models.CharField(max_length=16, choices=SUBNET_CHOICES)
    option_domain_name_servers = models.CharField(max_length=48, blank=True, null=True)
    option_domain_name = models.CharField(max_length=64, blank=True, null=True)
    option_routers = models.CharField(max_length=16, blank=True, null=True)
    def __unicode__(self):
        return self.scope_name

    class Meta:
        db_table = u'dhcp_scopes'


