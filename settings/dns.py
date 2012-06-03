MOZ_SITE_PATH = "/home/juber/sysadmins/dnsconfig/zones/mozilla.com/"
REV_SITE_PATH = "/home/juber/sysadmins/dnsconfig/zones/in-addr/"

ZONE_PATH = "/home/juber/sysadmins/dnsconfig/"

# Some hosts have there hostname as something like *.mozilla.com.mozilla.com.
# This can befixed by adding the control key 'nic.X.dns_auto_hostname': False.
# If FIX_M_C_M_C (fix Mozilla.Com.Mozilla.Com) is True, the control key will
# automatically be added to the system nic.
FIX_M_C_M_C = True

# All DNS data in SVN is being parsed. If this flag is True, that data will
# have sanity checks ran on it.
RUN_SVN_STATS = True
