__import__('inventory_context')
from systems.models import System

import datetime

updates = [
    #["management.seamicro.phx1.mozilla.com", "3410NU000302000034", "1/6/2014"],  # noqa 512 atom nodes
    ["seamicro-a.r101-7.console.phx1.mozilla.com", "0112NU003401000632", "2/14/2015", '1/1/2013'],  # noqa 64 xeon nodes
    ["seamicro-b.r101-7.console.phx1.mozilla.com", "1012NU003401000646", "6/28/2015", '1/1/2013'],  # noqa 64 xeon nodes
    ["seamicro-a.r301-3.console.phx1.mozilla.com", "1012NU003401000649", "9/27/2015", '1/1/2013'],  # noqa 64 xeon nodes
    ["seamicro-a1.r101-3.console.scl3.mozilla.com", "4811NU003201000621", "2/1/2015", '1/1/2013'],  # noqa 64 xeon nodes
    ["seamicro-b1.r101-3.console.scl3.mozilla.com", "4811NU003201000622", "2/1/2015", '1/1/2013'],  # noqa 64 xeon nodes
    ["seamicro-a1.r102-3.console.scl3.mozilla.com", "1012NU003401000658", "9/27/2015", '1/1/2013'],  # noqa 64 xeon nodes
    ["seamicro-c1.r101-3.console.scl3.mozilla.com", "1012NU003401000651", "6/28/2015", '1/1/2013'],  # noqa 64 xeon nodes
    # 4210NU000303000047? 1/6/2014  # 512 atom nodes
]


def n(name):
    return name.replace('console.', '')


def d(date):
    return datetime.datetime.strptime(date, '%m/%d/%Y')

s_count = 0


def set_warranty_for_chassis(chassis, warranty):
    ss = chassis.system_rack.systems().filter(
        oob_ip__icontains=chassis.oob_ip.strip('ssh').strip()
    )
    print "Systems belonging to this chassis...."
    for s in ss:
        if not s.warranty_end:
            global s_count
            s_count += 1

        print "\t%s" % s.hostname
        s.warranty_start, s.warranty_end = warranty
        s.save()


def main():
    for update in updates:
        hn, serial, warranty_end, warranty_start = (
            update[0], update[1], d(update[2]), d(update[3])
        )

        try:
            s = None
            s = System.objects.get(hostname=hn)
            hostname = hn
        except System.DoesNotExist:
            pass

        if not s:
            try:
                s = None
                s = System.objects.get(hostname=n(hn))
                hostname = n(hn)
            except System.DoesNotExist:
                print "No system in Inventory with hostname '%s' or '%s'" % (
                    hostname, n(hostname)
                )
                continue

        print "Updating warranty info for %s chassis -- expires %s" % (
            hostname, update[2]
        )
        set_warranty_for_chassis(s, [warranty_start, warranty_end])
    global s_count
    print "%s had their warranty end date set" % s_count

if __name__ == '__main__':
    main()
