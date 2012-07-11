from core.site.models import Site
from core.vlan.models import Vlan
from core.network.models import Network
from core.network.utils import calc_parent
from core.range.models import Range
import pdb
import ipaddr


sites = []

site_name = "scl1"
s,_ = Site.objects.get_or_create(name=site_name)
sites.append(s)

site_name = "scl2"
s,_ = Site.objects.get_or_create(name=site_name)
sites.append(s)

site_name = "scl3"
s,_ = Site.objects.get_or_create(name=site_name)
scl3 = s
sites.append(s)

site_name = "ams1"
s,_ = Site.objects.get_or_create(name=site_name)
sites.append(s)

site_name = "phx1"
s,_ = Site.objects.get_or_create(name=site_name)
phx1 = s
sites.append(s)

site_name = "sjc1"
s,_ = Site.objects.get_or_create(name=site_name)
sites.append(s)

site_name = "releng"
s,_ = Site.objects.get_or_create(name=site_name)
s.parent = scl3
s.save()
sites.append(s)

site_name = "mtv1"
s,_ = Site.objects.get_or_create(name=site_name)
sites.append(s)

site_name = "pek1"
s,_ = Site.objects.get_or_create(name=site_name)
sites.append(s)

site_name = "corp"
s,_ = Site.objects.get_or_create(name=site_name)
s.parent = phx1
s.save()
sites.append(s)


site_networks = []

ams1 = "10.4.0.0/16"
ams1_oct = "4"
n_str = ams1
n, _ = Network.objects.get_or_create(network_str=n_str, ip_type='4')
n.site = Site.objects.get(name="ams1")
n.save()
site_networks.append(n)

scl1 = "10.12.0.0/16"
scl1_oct = "12"
n_str = scl1
n, _ = Network.objects.get_or_create(network_str=n_str, ip_type='4')
n.site = Site.objects.get(name="scl1")
n.save()
site_networks.append(n)

scl2 = "10.14.0.0/16"
scl2_oct = "14"
n_str = scl2
n, _ = Network.objects.get_or_create(network_str=n_str, ip_type='4')
n.site = Site.objects.get(name="scl2")
n.save()
site_networks.append(n)

pek1 = "10.6.0.0/16"
pek1_oct = "6"
n_str = pek1
n, _ = Network.objects.get_or_create(network_str=n_str, ip_type='4')
n.site = Site.objects.get(name="pek1")
n.save()
site_networks.append(n)

phx1 = "10.8.0.0/16"
phx1_oct = "8"
n_str = phx1
n, _ = Network.objects.get_or_create(network_str=n_str, ip_type='4')
n.site = Site.objects.get(name="phx1")
n.save()
site_networks.append(n)

svc_phx1 = "10.10.0.0/16"
svc_phx1_oct = "10"
n_str = svc_phx1
n, _ = Network.objects.get_or_create(network_str=n_str, ip_type='4')
n.site = Site.objects.get(name="phx1")
n.save()
site_networks.append(n)

scl2_bid = "10.16.0.0/16"
scl2_bid_oct = "16"
n_str = scl2_bid
n, _ = Network.objects.get_or_create(network_str=n_str, ip_type='4')
n.site = Site.objects.get(name="scl2")
n.save()
site_networks.append(n)

phx1_bid = "10.18.0.0/16"
phx1_bid_oct = "18"
n_str = phx1_bid
n, _ = Network.objects.get_or_create(network_str=n_str, ip_type='4')
n.site = Site.objects.get(name="phx1")
n.save()
site_networks.append(n)

corp_phx1 = "10.20.0.0/16"
corp_phx1_oct = "20"
n_str = corp_phx1
n, _ = Network.objects.get_or_create(network_str=n_str, ip_type='4')
n.site = Site.objects.get(name="phx1")
n.save()
site_networks.append(n)

scl3 = "10.22.0.0/16"
scl3_oct = "22"
n_str = scl3
n, _ = Network.objects.get_or_create(network_str=n_str, ip_type='4')
n.site = Site.objects.get(name="scl3")
n.save()
site_networks.append(n)

pek1 = "10.24.0.0/16"
pek1_oct = "24"
n_str = pek1
n, _ = Network.objects.get_or_create(network_str=n_str, ip_type='4')
n.site = Site.objects.get(name="pek1")
n.save()
site_networks.append(n)

releng_scl3 = "10.26.0.0/16"
releng_scl3_oct = "26"
n_str = releng_scl3
n, _ = Network.objects.get_or_create(network_str=n_str, ip_type='4')
n.site = Site.objects.get(name="scl3")
n.save()
site_networks.append(n)

Ops_EC2_VPC = "10.128.0.0/16"
Ops_EC2_VPC_oct = "128"
n_str = Ops_EC2_VPC
n, _ = Network.objects.get_or_create(network_str=n_str, ip_type='4')
site_networks.append(n)

RelEng_EC2_VPC = "10.130.0.0/16"
RelEng_EC2_VPC_oct = "130"
n_str = RelEng_EC2_VPC
n, _ = Network.objects.get_or_create(network_str=n_str, ip_type='4')
site_networks.append(n)

AirMo_Ev = "10.255.0.0/16"
AirMo_Ev_oct = "255"
n_str = AirMo_Ev
n, _ = Network.objects.get_or_create(network_str=n_str, ip_type='4')
site_networks.append(n)


def create_network_vlan(v_num, v_name, n_str, site_octs, router_label=None):
    print "##### {0} {1} ##### {2} #####".format(v_num, v_name, n_str,
        site_octs)

    v, _ = Vlan.objects.get_or_create(number = v_num, name=v_name)

    for so in site_octs:
        n, _ = Network.objects.get_or_create(network_str=n_str.format(so), ip_type='4')
        n.vlan = v
        parent = calc_parent(n)
        if parent:
            n.site = parent.site
        n.save()
        ip = ipaddr.IPv4Network(n_str.format(so))
        if int(n_str[-2:]) >= 22:
            r, _ = Range.objects.get_or_create(start_str =
                    str(ipaddr.IPv4Address(int(ip.network) + 10)), end_str =
                    str(ipaddr.IPv4Address(int(ip.broadcast)
                    - 2)), network = n)


##### 17 console ##### 10.DC.17.0/24 #####
v_num = 17
v_name = "console"

n_str = "10.{0}.17.0/24"
site_octs = [scl1_oct]
create_network_vlan(v_num, v_name, n_str, site_octs)

##### 24 metrics ##### 10.DC.24.0/22 #####

v_num = 24
v_name = "metrics"

n_str = "10.{0}.24.0/22"
site_octs = [scl3_oct]
create_network_vlan(v_num, v_name, n_str, site_octs)

##### 28 stage.metrics ##### 10.DC.28.0/22 #####

v_num = 28
v_name = "stage.metrics"

n_str = "10.{0}.28.0/22"
site_octs = [scl3_oct]
create_network_vlan(v_num, v_name, n_str, site_octs)

##### 32 seamicro ##### 10.DC.32.0/23 #####

v_num = 23
v_name = "seamicro"

n_str = "10.{0}.32.0/23"
site_octs = [phx1_oct]
create_network_vlan(v_num, v_name, n_str, site_octs)

##### 40 winbuild ##### 10.DC.40.0/22 #####

v_num = 40
v_name = "winbuild"

n_str = "10.{0}.40.0/22"
site_octs = [scl1_oct]
# TODO, site_octs need to include relenge? which one?
create_network_vlan(v_num, v_name, n_str, site_octs)


##### 47 amotest ##### 10.DC.47.0/24 #####

v_num = 47
v_name = "amotest"

n_str = "10.{0}.47.0/24"
site_octs = [scl1_oct]
# TODO, site_octs need to include relenge? which one?
create_network_vlan(v_num, v_name, n_str, site_octs)

##### 49 ad.db ##### 10.DC.69.0/24 #####

v_num = 49
v_name = "ad.db"

n_str = "10.{0}.69.0/24"
site_octs = [scl3_oct]
create_network_vlan(v_num, v_name, n_str, site_octs)

##### 70 db ##### 10.DC.70.0/24 #####

v_num = 70
v_name = "db"

n_str = "10.{0}.70.0/24"
site_octs = [pek1_oct, phx1_oct, corp_phx1_oct]
create_network_vlan(v_num, v_name, n_str, site_octs)

net = Network.objects.get(network_str = n_str.format(corp_phx1_oct))
phx1 = Site.objects.get(name="phx1")
correct_site = Site.objects.get(name="corp", parent=phx1)
net.site = correct_site
net.save()

##### 71 build ##### ????????? #####

##### 72 shared ##### 10.DC.72.0/24 #####

v_num = 72
v_name = "shared"
router_label = "corpdmz"

n_str = "10.{0}.72.0/24"
#site_octs = [sjc1_oct, scl3_oct, corp_phx1_oct]
site_octs = [scl3_oct, corp_phx1_oct]
create_network_vlan(v_num, v_name, n_str, site_octs, router_label)

##### 73 qa ##### 10.DC.73.0/24 #####

v_num = 73
v_name = "qa"
router_label = None

n_str = "10.{0}.72.0/24"
#site_octs = [sjc1_oct, scl2_oct, scl3_oct, phx1]
site_octs = [scl2_oct, scl3_oct, phx1_oct]
# NOTE: "see 273?" The fuck does that mean?
create_network_vlan(v_num, v_name, n_str, site_octs, router_label)

##### 74 dmz ##### 10.DC.74.0/24 #####

v_num = 74
v_name = "dmz"
router_label = None

n_str = "10.{0}.74.0/24"
site_octs = [scl3_oct, releng_scl3_oct, pek1_oct, phx1_oct]
create_network_vlan(v_num, v_name, n_str, site_octs, router_label)

##### 75 private ##### 10.DC.75.0/24 #####

v_num = 75
v_name = "private"
router_label = "internal"

n_str = "10.{0}.75.0/24"
site_octs = [scl1_oct, scl2_oct, scl3_oct, pek1_oct, corp_phx1_oct, phx1_oct]
# Note: for scl1,  label = infra
create_network_vlan(v_num, v_name, n_str, site_octs, router_label)

##### 76 sandbox ##### 10.DC.76.0/24 #####

v_num = 76
v_name = "sandbox"
router_label = "ssandbox"

n_str = "10.{0}.76.0/24"
site_octs = [scl1_oct, scl2_oct, scl3_oct, phx1_oct]
# Note: for scl1,  label = infra
create_network_vlan(v_num, v_name, n_str, site_octs, router_label)

##### 77 mail ##### 10.DC.77.0/24 #####

v_num = 77
v_name = "mail"
router_label = None

n_str = "10.{0}.77.0/24"
site_octs = [pek1_oct, corp_phx1_oct]
create_network_vlan(v_num, v_name, n_str, site_octs, router_label)

##### 80 static ##### 10.DC.80.0/24 #####

v_num = 80
v_name = "mail"
router_label = "web"

n_str = "10.{0}.80.0/24"
site_octs = [scl2_oct, scl3_oct, pek1_oct, phx1_oct]
create_network_vlan(v_num, v_name, n_str, site_octs, router_label)

##### 81 webapp ##### 10.DC.81.0/24 #####

v_num = 81
v_name = "webapp"
router_label = "app-generic"

n_str = "10.{0}.81.0/24"
site_octs = [scl2_oct, scl3_oct, pek1_oct, phx1_oct]
create_network_vlan(v_num, v_name, n_str, site_octs, router_label)

##### 82 bugs ##### 10.DC.82.0/24 #####

v_num = 82
v_name = "bugs"
router_label = "app-bugs"

n_str = "10.{0}.82.0/24"
site_octs = [scl2_oct, scl3_oct, pek1_oct, phx1_oct]
create_network_vlan(v_num, v_name, n_str, site_octs, router_label)

##### 83 addons ##### 10.DC.83.0/24 #####

v_num = 83
v_name = "addons"
router_label = "app-amo"

n_str = "10.{0}.83.0/24"
# Note: instead of a check, scl has 'addons'
site_octs = [scl2_oct, scl3_oct, pek1_oct, phx1_oct]
create_network_vlan(v_num, v_name, n_str, site_octs, router_label)

##### 84 dist ##### 10.DC.84.0/24 #####

v_num = 84
v_name = "dist"
router_label = "app-dist"

n_str = "10.{0}.84.0/24"
site_octs = [scl2_oct, scl3_oct, pek1_oct, phx1_oct]
create_network_vlan(v_num, v_name, n_str, site_octs, router_label)

##### 85 stage.bugs ##### 10.DC.85.0/24 #####

v_num = 84
v_name = "stage.bugs"
router_label = "app-bugs-stage"

n_str = "10.{0}.85.0/24"
site_octs = [scl3_oct]
create_network_vlan(v_num, v_name, n_str, site_octs, router_label)

##### 100 metrics ##### 10.DC.100.0/23 #####

v_num = 100
v_name = "metrics"
router_label = None

n_str = "10.{0}.100.0/23"
#site_octs = [mtv1_oct, phx1_oct]
# TODO, what is the mtv network?
site_octs = [phx1_oct]
create_network_vlan(v_num, v_name, n_str, site_octs, router_label)

##### 118 labs ##### 10.110.8.0/24 #####

v_num = 118
v_name = "labs"
router_label = "labs-pancake"

n_str = "10.{0}.100.0/24"
#site_octs = [sjc1_oct]
# TODO, no sjc1 network
#create_network_vlan(v_num, v_name, n_str, site_octs, router_label)

##### 120 ateam ##### 10.DC.120.0/24 #####

v_num = 120
v_name = "ateam"
router_label = None

n_str = "10.{0}.120.0/24"
#site_octs = [mtv1_oct, phx1_oct]
# TODO, what is the mtv network?
site_octs = [phx1_oct]
create_network_vlan(v_num, v_name, n_str, site_octs, router_label)

##### 121 bughunter ##### 10.DC.121.0/24 #####

v_num = 121
v_name = "bughunter"
router_label = None

n_str = "10.{0}.121.0/24"
site_octs = [phx1_oct]
create_network_vlan(v_num, v_name, n_str, site_octs, router_label)
