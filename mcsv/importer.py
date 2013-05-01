import operator
import re
import StringIO
import csv

from django.core.exceptions import ValidationError
from mcsv.resolver import Resolver
from systems import models as sys_models

# XXX so much stripping going on


class MockSystem(object):
    """
    A fake system where we can stage changes
    """
    pass


class Generator(object):
    def __init__(self, resolver, headers, delimiter=','):
        # TODO, use stdlib module csv
        self.r = resolver
        self.headers = headers
        self.delimiter = ','

        self.meta_bundles = [
            (handle, b(self.r))
            for handle, b
            in self.r.metas.iteritems()
        ]

        self.system_attr_bundles = [
            (handle, b(self.r))
            for handle, b
            in self.r.system_attrs.iteritems()
        ]

        self.system_related_bundles = [
            (handle, b(self.r))
            for handle, b
            in self.r.system_relateds.iteritems()
        ]

        self.system_kv_bundles = [
            (handle, b(self.r))
            for handle, b
            in self.r.system_kvs.iteritems()
        ]
        """
        Here we want to make a list of callbacks that will get chained into one
        another.

        Phase 0)
        These are meta headers. They set attributes that are not saved to an
        the database.

        Phase 1)
        System attr headers will have an new system model pushed through their
        handlers and they will set attributes.

        Phase 2)
        System related headers will have a system model (may or maynot have a
        pk) pushed through their handlers and they will set the correct values
        on the system.

        Phase 3)
        System key values will have their system attribute set and then may or
        maynot be saved.
        """
        bundle_lists = [
            self.meta_bundles, self.system_attr_bundles,
            self.system_related_bundles, self.system_kv_bundles
        ]
        action_list = []
        fail = False
        for (header, raw_header) in headers:
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
                        # related attributes use raw_header
                        action_list.append(
                            (phase, raw_header, bundle['handler'])
                        )
                        found_handler = True
                        break  # Break the inner loop

            if found_handler:
                continue
            fail = "Couldn't find handler for header {0}".format(header)
        if fail:
            raise ValidationError(fail)
        self.action_list = action_list

    def handle(self, data):
        """
        Where the magic happens.
        """
        phase_0 = []
        phase_1 = []
        phase_2 = []
        phase_3 = []
        for (phase, header, action), item in zip(self.action_list, data):
            if phase == 0:
                phase_0.append((action, header, item))
            elif phase == 1:
                phase_1.append((action, item))
            elif phase == 2:
                phase_2.append((action, header, item))
            elif phase == 3:
                phase_3.append((action, header, item))
            else:
                raise ValidationError("wut?")

        s = MockSystem()
        # Phase 0 meta headers
        for action, header, item in phase_0:
            s = action(s, header, item)

        # Phase 1 System attributes
        for action, item in phase_1:
            s = action(s, item)

        # Phase 2 Related fields
        for action, header, item in phase_2:
            s = action(s, header, item)

        # Phase 3 key value paires
        kv_cbs = []  # keyvalue call backs
        for action, key, value in phase_3:
            def keyvalue_cb(system, key=key, value=value, save=True):
                orig_kv = None
                if not system.pk:
                    # It has to be a new key
                    kv = sys_models.KeyValue(
                        system=system, key=key, value=value
                    )
                else:
                    # Attempt to find an existing key first
                    try:
                        kv = system.keyvalue_set.get(key=key)
                        kv.value = value
                        orig_kv = system.keyvalue_set.get(pk=kv.pk)
                    except system.keyvalue_set.model.DoesNotExist:
                        kv = sys_models.KeyValue(
                            system=system, key=key, value=value
                        )
                if save:
                    kv.save()
                return kv, orig_kv

            # Set the function name for debugging purposes
            keyvalue_cb.__name__ = "{0} {1}".format(key, value)

            kv_cbs.append(keyvalue_cb)

        return s, kv_cbs


def csv_import(csv_text, save=True, primary_attr='hostname'):
    r = Resolver()
    generator = None

    def make_header(header):
        # sometimes headers have a '%' in them. We want everything to the
        # left of the first '%'
        return map(lambda s: s.strip().lower(), (header.split('%')[0], header))

    ret = []
    f = StringIO.StringIO(csv_text)
    reader = csv.reader(f, delimiter=',', quotechar='"')

    def has_something(line):
        return reduce(lambda a, b: b or a, line, False)

    for line in [map(lambda s: s.strip(), line) for line in reader]:
        if not has_something(line):  # allow blank lines
            continue
        if not generator:
            generator = Generator(
                r, [make_header(header) for header in line]
            )
            continue
        mock_s, kv_callbacks = generator.handle(line)
        try:
            if hasattr(mock_s, '_primary_attr'):
                get_params = {
                    mock_s._primary_attr: mock_s._primary_value
                }
            else:
                get_params = {
                    primary_attr: getattr(mock_s, primary_attr)
                }

            s = sys_models.System.objects.get(**get_params)
            orig_system = sys_models.System.objects.get(pk=s.pk)

            for attr, value in vars(mock_s).iteritems():
                if attr.startswith('_'):
                    continue
                setattr(s, attr, value)

        except sys_models.System.DoesNotExist:
            s = sys_models.System(**vars(mock_s))
            orig_system = None

        if save:
            s.save()
        kvs = []
        for cb in kv_callbacks:
            kvs.append(cb(s, save=save))
        ret.append({'system': s, 'orig_system': orig_system, 'kvs': kvs})
    return ret


def main(fname):
    host = "http://toolsdev1.dmz.scl3.mozilla.com:8000"
    query = host + '/en-US/core/search/#q'
    with open(fname, 'r') as fd:
        csv_import(fd.readlines())

    print query.strip(' OR ')
