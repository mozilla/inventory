#!/usr/bin/python
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))
import manage
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.base'
import manage
from core.range.models import Range, RangeKeyValue
from core.interface.static_intr.models import StaticInterface
from mozdns.address_record.models import AddressRecord
from django.db.models import Q
from core.range.forms import RangeForm
from core.range.models import Range, RangeKeyValue
from core.interface.static_intr.models import StaticInterface
from mozdns.address_record.models import AddressRecord
from mozdns.ptr.models import PTR
from mozdns.ip.models import ipv6_to_longs
from core.views import CoreDeleteView, CoreDetailView
from core.views import CoreCreateView, CoreUpdateView, CoreListView
from core.keyvalue.utils import get_attrs, update_attrs, get_aa, get_docstrings
from core.keyvalue.utils import get_docstrings, dict_to_kv
import ipaddr
import simplejson as json
from core.interface.static_intr.views import do_combine_a_ptr_to_interface
from django.test import Client
from systems.models import System
#(addr, ptr, system, mac_address):
def main():
    for mrange in Range.objects.all():
        print "Now starting on Range %s" % mrange
        attrs = mrange.rangekeyvalue_set.all()

        start_upper, start_lower = mrange.start_upper, mrange.start_lower
        end_upper, end_lower = mrange.end_upper, mrange.end_lower

        gt_start = Q(ip_upper=start_upper, ip_lower__gte=start_lower)
        gt_start = gt_start | Q(ip_upper__gte=start_upper)

        lt_end = Q(ip_upper=end_upper, ip_lower__lte=end_lower)
        lt_end = lt_end | Q(ip_upper__lte=end_upper)

        records = AddressRecord.objects.filter(gt_start, lt_end)
        ptrs = PTR.objects.filter(gt_start, lt_end)
        intrs = StaticInterface.objects.filter(gt_start, lt_end)

        range_data = []
        for i in range((start_upper << 64) + start_lower, (end_upper << 64) +
                end_lower - 1):
            taken = False
            adr_taken = None
            ip_str = str(ipaddr.IPv4Address(i))
            for record in records:
                if record.ip_lower == i:
                    adr_taken = record
                    break

            ptr_taken = None
            for ptr in ptrs:
                if ptr.ip_lower == i:
                    ptr_taken = ptr
                    break

            if ptr_taken and adr_taken:
                if ptr_taken.name == adr_taken.fqdn:
                    range_data.append(('A/PTR', ip_str, ptr_taken, adr_taken))
                else:
                    range_data.append(('PTR', ip_str, ptr_taken))
                    range_data.append(('A', ip_str, adr_taken))
                taken = True
            elif ptr_taken and not adr_taken:
                range_data.append(('PTR', ip_str, ptr_taken))
                taken = True
            elif not ptr_taken and adr_taken:
                range_data.append(('A', ip_str, adr_taken))
                taken = True

            for intr in intrs:
                if intr.ip_lower == i:
                    range_data.append(('Interface', ip_str, intr))
                    taken = True
                    break

            if taken == False:
                range_data.append((None, ip_str))
        client = Client()
        for bl in range_data:
            system_hostname = ''
            try:
                system = System.objects.get(hostname=bl[2].name.replace(".mozilla.com", ""))
                print system.hostname
                addr = AddressRecord.objects.get(pk=bl[3].pk)
                ptr = PTR.objects.get(pk=bl[2].pk)
                do_combine_a_ptr_to_interface(addr, ptr, system, "00:00:00:00:00:00")
                #client.post('/en-US/core/interface/combine_a_ptr_to_interface/%i/%i/' % (bl[3].pk, bl[2].pk), data={'is_ajax' : 1, 'system_hostname': bl[2].name.replace(".mozilla.com", "")})
            except Exception, e:
                print e
if __name__ == '__main__':
    main()

