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
            print "[New Allocation] {0}".format(a)

        if created:
            print "Created new allocation {0}".format(a)
        uf = row['Frequency of Usage'].strip().lower()

        if uf == "not much now; soon, constantly":
            uf = 'constantly'

        if uf == 'periodic':
            uf = 'periodicly'

        if row['Proper name'].startswith('builddata.pub.build.mozilla.org'):
            name = "releng web tools"
        else:
            name = row['Proper name'].strip().lower()

        if not name:
            print "Skipping.... '{0}'".format(row)

        sites = row['Locations'].split(',')

        save_services(name, sites, uf, a, row)


def save_services(name, sites, uf, a, row):
    if not sites:
        s, created = Service.objects.get_or_create(
            name=name,
            alias=row['Alias names'].strip().lower(),
            description=row['Description'].strip(),
            business_owner=row['Business Owner\n'].strip().title() or 'Unknown',  # noqa
            used_by=row['Used By'].strip() or 'unknown',
            usage_frequency=uf or 'unknown',
            impact=row['Impact'].strip().lower() or 'low',
            category=row['Category'].strip().lower().title() or 'Unknown',
            tech_owner=(
                row['Tech Owner'].strip().lower().title() or 'Unknown'
            ),
            site=None
        )

        if a:
            s.allocations.add(a)
            s.save()

        if created:
            print "Created new service {0}".format(s)

    elif len(sites) == 1:
        if sites[0].lower() == 'saas' or not sites[0].strip():
            site = None
        else:
            try:
                site = Site.objects.get(
                    full_name=sites[0]
                )
            except Site.DoesNotExist:
                raise Exception(
                    "For service {0} no site '{1}' found in "
                    "Inventory".format(name, sites[0])
                )

        s, created = Service.objects.get_or_create(
            name=name,
            alias=row['Alias names'].strip().lower(),
            description=row['Description'].strip(),
            business_owner=row['Business Owner\n'].strip().title() or 'Unknown',  # noqa
            used_by=row['Used By'].strip() or 'unknown',
            usage_frequency=uf or 'unknown',
            impact=row['Impact'].strip().lower() or 'low',
            category=row['Category'].strip().lower().title() or 'Unknown',
            tech_owner=(
                row['Tech Owner'].strip().lower().title() or 'Unknown'
            ),
            site=site
        )

        if a:
            s.allocations.add(a)
            s.save()

        if created:
            print "Created new service {0}".format(s)
    else:
        # We have multiple sites so create a parent site to assign to all the
        # child sites. Child sites will have a minimal amount of information
        # (i.e. no "Buisness Onwer"). The parent service will be the most
        # descriptive to attempt to deduplicate data.
        parent_service, created = Service.objects.get_or_create(
            name=name,
            alias=row['Alias names'].strip().lower(),
            description=row['Description'].strip(),
            business_owner=row['Business Owner\n'].strip().title() or 'Unknown',  # noqa
            used_by=row['Used By'].strip() or 'unknown',
            usage_frequency=uf or 'unknown',
            impact=row['Impact'].strip().lower() or 'low',
            category=row['Category'].strip().lower().title() or 'Unknown',
            tech_owner=(
                row['Tech Owner'].strip().lower().title() or 'Unknown'
            ),
            site=None
        )
        for site in sites:
            try:
                site = Site.objects.get(
                    full_name=site.lower().strip()
                )
            except Site.DoesNotExist:
                raise Exception(
                    "For service {0} no site '{1}' found in "
                    "Inventory".format(name, sites)
                )
            s, created = Service.objects.get_or_create(
                name=name,
                alias=row['Alias names'].strip().lower(),
                site=site,
                parent_service=parent_service
            )

            if a:
                s.allocations.add(a)
                s.save()

            if created:
                print "Created new service {0}".format(s)

if __name__ == '__main__':
    Site.objects.get_or_create(full_name='ovh')

    with open(sys.argv[1], 'r') as csvfile:
        simport(csv.DictReader(csvfile))
