__import__('inventory_context')

from systems.models import System


def make_unique_keys(s):
    all_kvs = {}

    def add(kv):
        all_kvs.setdefault(kv.key, []).append(kv)

    map(add, s.keyvalue_set.all())
    first = True
    for key, kvs in all_kvs.iteritems():
        if len(kvs) > 1:
            # Keep track of the key value a pair with the highest primary key.
            # All other keys will be deleted
            max_pk_key = max(kvs, key=lambda kv: kv.pk)

            if first:
                print "Loooking at host: %s  https://inventory.mozilla.org%s" % (  # noqa
                    s.hostname, s.get_absolute_url())
            first = False
            print "%s has duplicate keys %s" % (key, kvs)
            for kv in kvs:
                if kv != max_pk_key:
                    print "Deleting %s" % kv
                    kv.delete()
    if not first:
        print ""


for s in System.objects.filter(hostname__endswith='tegra.releng.scl3.mozilla.com'):  # noqa
    make_unique_keys(s)
