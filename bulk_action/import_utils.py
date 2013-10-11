from django.db.models.fields.related import ForeignKey

from systems.models import System
from core.registration.static.models import StaticReg
from core.hwadapter.models import HWAdapter

from mozdns.utils import ensure_label_domain

import decimal
import datetime
import simplejson as json


class BadImportData(Exception):
    def __init__(self, bad_blob=None, msg=''):
        self.bad_blob = bad_blob
        self.msg = msg
        return super(BadImportData, self).__init__()


class BadUpdateCreate(BadImportData):
    pass


class BAEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        elif isinstance(o, datetime.datetime) or isinstance(o, datetime.date):
            return o.isoformat()
        super(BAEncoder, self).default(o)


class BADecoder(json.JSONDecoder):
    pass


def dumps(j):
    return json.dumps(j, cls=BAEncoder)


def loads(j):
    return json.loads(j, cls=BADecoder)


def make_save(obj, blob):
    def save():
        obj.save()
        if 'pk' in blob:
            assert blob['pk'] == obj.pk
        else:
            blob['pk'] = obj.pk
    return save


def recurse_confirm_no_pk(blob):
    for attr, value in blob.iteritems():
        if isinstance(value, list) and attr != 'views':
            # the views attr is always a list of ints, no need to check for pk
            for sub_blob in value:
                recurse_confirm_no_pk(sub_blob)
        elif attr == 'pk':
            raise BadUpdateCreate()


def system_import(blob):
    if 'pk' in blob:
        try:
            system = System.objects.get(pk=blob['pk'])
            return system_update(system, blob)
        except System.DoesNotExist:
            raise BadImportData(
                bad_blob=blob,
                msg='Could not find the System with primary key '
                '{0}.'.format(blob['pk'])
            )
    else:
        try:
            recurse_confirm_no_pk(blob)
            system = System()
            return system_update(system, blob)
        except BadUpdateCreate:
            raise BadImportData(
                bad_blob=blob,
                msg='This object is new (it has no pk) but other objects tied '
                'to it have pk values. This is not allowed.'
            )


def sreg_import(system, blob):
    if 'pk' in blob:
        try:
            sreg = StaticReg.objects.get(pk=blob['pk'])
            return sreg_update(sreg, blob)
        except StaticReg.DoesNotExist:
            raise BadImportData(
                bad_blob=blob,
                msg='Could not find the Static Registration with primary key '
                '{0}.'.format(blob['pk'])
            )
    else:
        try:
            recurse_confirm_no_pk(blob)
            sreg = StaticReg(system=system)
            return sreg_update(sreg, blob)
        except BadUpdateCreate:
            raise BadImportData(
                bad_blob=blob,
                msg='This object is new (it has no pk) but other objects tied '
                'to it have pk values. This is not allowed.'
            )


def hw_import(sreg, blob):
    if 'pk' in blob:
        try:
            hw = HWAdapter.objects.get(pk=blob['pk'])
            return hw_update(hw, blob)
        except StaticReg.DoesNotExist:
            raise BadImportData(
                bad_blob=blob,
                msg='Could not find the Hardware Adapter with primary key '
                '{0}.'.format(blob['pk'])
            )
    else:
        try:
            recurse_confirm_no_pk(blob)
            hw = HWAdapter(sreg=sreg)
            return hw_update(hw, blob)
        except BadUpdateCreate:
            raise BadImportData(
                bad_blob=blob,
                msg='This object is new (it has no pk) but other objects tied '
                'to it have pk values. This is not allowed.'
            )


def import_kv(obj, blobs):
    save_functions = []
    Klass = obj.keyvalue_set.model
    for blob in blobs:
        if 'pk' in blob:
            try:
                kv = Klass.objects.get(pk=blob['pk'])
            except Klass.DoesNotExist:
                raise BadImportData(
                    bad_blob=blob,
                    msg='Could not find the Key Value pair with primary key '
                    '{0}.'.format(blob['pk'])
                )
            save_functions += update_kv(kv, blob)
        else:
            kv = Klass(obj=obj)
            save_functions += update_kv(kv, blob)
    return save_functions


def update_kv(kv, blob):
    try:
        kv.key, kv.value = blob['key'], blob['value']
    except KeyError:
        raise BadImportData(
            bad_blob=blob,
            msg="Either the 'key' or 'value' attribute is missing from this "
            "blob. Both are required for KeyValue pairs."
        )

    def save():
        # Refresh the cash with an actual object
        kv.obj = kv.obj.__class__.objects.get(pk=kv.obj.pk)
        make_save(kv, blob)()

    return [(4, save)]


def hw_update(hw, blob):
    save_functions = []
    for attr, value in blob.iteritems():
        if attr == 'keyvalue_set':
            save_functions += import_kv(hw, value)
        else:
            setattr(hw, attr, value)

    def save():
        # Refresh the cash with an actual object
        hw.sreg = StaticReg.objects.get(pk=hw.sreg.pk)
        make_save(hw, blob)()

    return [(3, save)] + save_functions


def sreg_update(sreg, blob):
    save_functions = []
    for attr, value in blob.iteritems():
        if attr == 'hwadapter_set':
            if not isinstance(value, list):
                raise BadImportData(
                    bad_blob=blob,
                    msg='The Static Registration attribute hwadapter_set must '
                    'a list of Hardware Adapter JSON blobs'
                )
            for hw_blob in value:
                save_functions += hw_import(sreg, hw_blob)
        elif attr == 'keyvalue_set':
            save_functions += import_kv(sreg, value)
        elif attr == 'views':
            continue  # We handle views in save since new objects need a pk
        else:
            setattr(sreg, attr, value)

    def save():
        # This code runs in a transaction that is rolled back if an exception
        # is raised.
        sreg.label, sreg.domain = ensure_label_domain(sreg.fqdn)
        # So this is strange, but probably reasonable due to the face we are
        # using so many closers and aliasing objects left and right. We need to
        # update set the system again or else sreg.system ends up being None.
        sreg.system = System.objects.get(pk=sreg.system.pk)
        make_save(sreg, blob)()
        # Now save the views
        for view in blob['views']:
            sreg.views.add(view)

    return [(2, save)] + save_functions


def system_update(system, blob):
    save_functions = []
    for attr, value in blob.iteritems():
        if attr == 'staticreg_set':
            if not isinstance(value, list):
                raise BadImportData(
                    bad_blob=blob,
                    msg='The system attribute statirc_reg_set must a list of '
                    'Static Registration JSON blobs'
                )
            for sreg_blob in value:
                save_functions += sreg_import(system, sreg_blob)
        elif attr == 'keyvalue_set':
            save_functions += import_kv(system, value)
        else:
            set_field(system, attr, value)

    return [(1, make_save(system, blob))] + save_functions


def set_field(obj, attr, value):
    # yay side effects
    if attr == 'pk':  # Don't ever set a primary key
        return

    if hasattr(obj.__class__, attr):
        m_attr = getattr(obj.__class__, attr)
        if isinstance(m_attr.field, ForeignKey):
            m_value = m_attr.field.rel.to.objects.get(pk=value)
        else:
            raise Exception("Really bad error")
    else:
        m_value = value
    setattr(obj, attr, m_value)
