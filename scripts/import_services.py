__import__('inventory_context')

from core.service.models import Service
from core.site.models import Site

from systems.models import Allocation

import csv
import sys


def simport(reader):
    for row in reader:
        od = row['Owner - Department'].strip()
        if od:
            a, created = Allocation.objects.get_or_create(name=od)
        else:
            a = None

        if created:
            print "Created new allocation {0}".format(a)
        uf = row['Frequency of Usage'].strip().lower()

        if uf == "not much now; soon, constantly":
            uf = 'constantly'

        if uf == 'periodic':
            uf = 'periodicly'

        if row['Name'].startswith('builddata.pub.build.mozilla.org'):
            name = "releng web tools"
        else:
            name = row['Name'].strip().lower()

        try:
            site = Site.objects.get(
                full_name=row['Hosted Location'].lower().strip()
            )
        except Site.DoesNotExist:
            site = None

        s, created = Service.objects.get_or_create(
            name=name,
            description=row['Description'].strip(),
            business_owner=row['Business Owner\n'].strip().title() or 'Unknown',  # noqa
            used_by=row['Used By'].strip() or 'unknown',
            usage_frequency=uf or 'unknown',
            impact=row['Impact'].strip().lower() or 'low',
            category=row['Category'].strip().lower().title() or 'Unknown',
            tech_owner=row['Tech Owner'].strip().lower().title() or 'Unknown',
            site=site
        )

        if a:
            s.allocations.add(a)
            s.save()

        if created:
            print "Created new service {0}".format(s)

if __name__ == '__main__':

    with open(sys.argv[1], 'r') as csvfile:
        simport(csv.DictReader(csvfile))
