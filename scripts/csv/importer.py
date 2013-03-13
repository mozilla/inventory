import sys
import operator
import os
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                os.pardir, os.pardir)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import manage

from resolver import Resolver
from systems.models import *


class Generator(object):
    def __init__(self, resolver, headers, delimiter=','):
        self.r = resolver
        self.headers = headers
        self.delimiter = ','

        system_attr_bundles = [
            (handle, b(self.r))
            for handle, b
            in self.r.system_attrs.iteritems()
        ]

        system_related_bundles = [
            (handle, b(self.r))
            for handle, b
            in self.r.system_relateds.iteritems()
        ]

        system_kv_bundles = [
            (handle, b(self.r))
            for handle, b
            in self.r.system_kvs.iteritems()
        ]
        """
        Here we want to make a list of callbacks that will get chained into one
        another.

        Phase 0)
        System attr headers will have an new system model pushed through their
        handlers and they will set attributes.

        Phase 1)
        System related headers will have a system model (may or maynot have a
        pk) pushed through their handlers and they will set the correct values
        on the system.

        Phase 2)
        System key values will have their system attribute set and then may or
        maynot be saved.
        """
        bundle_lists = [
            system_attr_bundles, system_related_bundles, system_kv_bundles
        ]
        action_list = []
        fail = False
        for header in headers:
            found_handler = False

            for (phase, bundle_list) in enumerate(bundle_lists):
                for handle, bundle in bundle_list:
                    def re_in(header):
                        """
                        This function is only called when a bundle doesn't
                        define a match function ('match_func')
                        """
                        c = lambda el: bool(
                            re.search('^{0}$'.format(header), el)
                        )
                        return reduce(
                            operator.or_, map(c, bundle['values']), False
                        )

                    handler_matches = bundle.get('match_func', re_in)

                    if handler_matches(header):
                        action_list.append((phase, header, bundle['handler']))
                        found_handler = True
                        break  # Break the inner loop

            if found_handler:
                continue
            print "Couldn't find handler for header {0}".format(header)
            fail = True
        if fail:
            raise Exception()
        self.action_list = action_list

    def handle(self, line):
        """
        Where the magic happens.
        """
        data = [d.strip() for d in line.split(self.delimiter)]
        phase_0 = []
        phase_1 = []
        phase_2 = []
        for (phase, header, action), item in zip(self.action_list, data):
            if phase == 0:
                phase_0.append((action, item))
            elif phase == 1:
                phase_1.append((action, item))
            elif phase == 2:
                phase_2.append((action, header, item))
            else:
                raise Exception("wut?")

        # Phase 0 System attributes
        s = System()
        for action, item in phase_0:
            s = action(s, item)

        # Phase 1 Related fields
        for action, item in phase_1:
            s = action(s, item)

        # Phase 2 key value paires
        kv_cbs = []  # keyvalue call backs
        for action, key, value in phase_2:
            def keyvalue_cb(system, key=key, value=value):
                return KeyValue.objects.get_or_create(
                    system=system, key=key, value=value
                )[0]

            # Set the function name for debugging purposes
            keyvalue_cb.__name__ = key + ' ' + value
            kv_cbs.append(keyvalue_cb)

        return s, kv_cbs


def main(fname):
    r = Resolver()
    host = "http://toolsdev1.dmz.scl3.mozilla.com:8000"
    query = host + '/en-US/core/search/#q'
    with open(fname, 'r') as fd:
        generator = None
        for line in fd.readlines():
            if not generator:
                generator = Generator(
                    r, [l.strip().lower() for l in line.split(',')]
                )
                continue
            s, kv_callbacks = generator.handle(line)
            try:
                # Do this so we can run this multiple times
                existing = System.objects.get(hostname=s.hostname)
                s.pk = existing.pk  # Hackity hacky sack
            except System.DoesNotExist:
                pass
            s.save()

            for cb in kv_callbacks:
                cb(s)
            query += s.hostname + ' OR '

    print query.strip(' OR ')
