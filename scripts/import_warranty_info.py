__import__('inventory_context')
from systems.models import System
from slurpee.models import ExternalData
import datetime
import csv
import sys


def wimport(reader, lookups, date_format):
    total_records = 0
    updated = 0
    missing = 0
    external = 0
    for row in reader:
        total_records += 1
        warranty_start, warranty_end, serial = (
            row[lookups['warranty_start']], row[lookups['warranty_end']],
            row[lookups['serial']]
        )
        if not (warranty_start and warranty_end):
            print "No warranty info in line: {0}".format(row)
            continue

        if '/' in warranty_start:
            SP = '/'
        elif '-' in warranty_start:
            SP = '-'
        else:
            raise Exception("Cand determine date delimiter")

        warranty_start = SP.join(map(
            lambda s: s if len(s) != 1 else '0' + s, warranty_start.split(SP)
        ))
        warranty_end = SP.join(map(
            lambda s: s if len(s) != 1 else '0' + s, warranty_end.split(SP)
        ))
        serial = serial.strip("'")  # Not sure why there is a ' mark

        try:
            s = System.objects.get(serial=serial)
        except System.DoesNotExist:
            try:
                s = ExternalData.objects.get(name='serial', data=serial).system
                external += 1
            except ExternalData.DoesNotExist:
                print "No system in Inventory with serial '%s'" % serial
                missing += 1
                continue
        except System.MultipleObjectsReturned:
            print "Multiple system in Inventory with serial '%s'" % serial
            for s in System.objects.filter(serial=serial):
                print (
                    "\thttps://inventory.mozilla.org/systems/show/%s/ %s" %
                    (s.pk, s.hostname)
                )

        if not s.warranty_end:
            updated += 1
        try:
            s.warranty_start = datetime.datetime.strptime(
                warranty_start, date_format
            )
            s.warranty_end = datetime.datetime.strptime(
                warranty_end, date_format
            )
        except ValueError, e:
            print "Error: {0} in line: {1}".format(e, row)
            continue
        s.save()

    print "Total number of records in spreadsheet: %s" % total_records
    print "Total number of records that were not in Inventory: %s" % missing  # noqa
    print "Matched %s records" % (total_records - missing)  # noqa
    print "\nUpdated %s records who previously didn't have warranty info" % (updated)  # noqa
    print "\nUpdated %s records using external data for serial lookup" % (external)  # noqa

if __name__ == '__main__':

    def i(fname, lookups, date_format):
        print "%s Importing %s" % ('=' * 90, fname)
        with open(fname, 'r') as csvfile:
            wimport(csv.DictReader(csvfile), lookups, date_format)

    i(sys.argv[1], {
        'warranty_start': 'start',
        'warranty_end': 'end',
        'serial': 'serial'
    }, sys.argv[2])
