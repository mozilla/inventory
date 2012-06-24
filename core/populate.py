from core.site.models import Site
from core.vlan.models import Vlan
from core.network.models import Network


sites = []

for i in range(10):
    s = Site(name="site" + str(i))
    s.save()
    sites.append(s)

for i in range(10):
    n = Network(network_str = "10.{0}.0.0/16".format(str(i+(i*7 % 3))),
            ip_type='4')
    n.save()

    for i in range(10):
        for j in range(i):
            n.sites.add(sites[j])
    n.save()

for i in range(10):
    v = Vlan(vlan_number = i, vlan_name="vlan"+str(i))
    v.site = sites[i]
    v.save()
