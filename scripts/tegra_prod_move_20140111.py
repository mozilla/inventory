__import__('inventory_context')

from mozdns.address_record.models import AddressRecord
from mozdns.ptr.models import PTR
from mozdns.cname.models import CNAME

with open('tegra_prod_move.csv', 'r') as fd:
    for line in fd.readlines()[1:]:  # Skip the first line, its the header
        line = line.strip()
        if line.startswith('#') or not line:
            continue
        old_name, cname_fqdn, new_name = line.split(',')[:3]
        print line

        # Get the objects we want to manipulate
        old_a = AddressRecord.objects.get(fqdn=old_name)
        old_ptr = PTR.objects.get(name=old_name)
        cname = CNAME.objects.get(fqdn=cname_fqdn)

        # Make the changes
        cname.target = new_name
        cname.save()
        old_a.delete()
        old_ptr.delete()
