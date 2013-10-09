from django.db.models.fields.related import ForeignKey

from systems.models import System
from core.registration.static.models import StaticReg
from core.hwadapter.models import HWAdapter

import decimal
import datetime
import simplejson as json


class BadImportData(Exception):
    def __init__(self, bad_data=None, msg=''):
        self.bad_data = bad_data
        self.msg = msg
        return super(BadImportData).__init__()


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


def recurse_confirm_no_pk(blob):
    for attr, value in blob.iteritems():
        if isinstance(value, list):
            recurse_confirm_no_pk(value)
        elif attr == 'pk':
            raise BadUpdateCreate()


def system_import(blob):
    if 'pk' in blob:
        try:
            s = System.objects.get(pk=blob['pk'])
            return system_update(s, blob)
        except System.DoesNotExist:
            raise BadImportData(
                bad_blob=blob,
                msg='Could not find the System with primary key '
                '{0}.'.format(blob['pk'])
            )
    else:
        try:
            recurse_confirm_no_pk(blob)
            s = System()
            return system_update(s, blob)
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
            return sreg_update(sreg, system, blob)
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
            return hw_update(hw, sreg, blob)
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


def import_kv(obj, values):
    # TODO implment this
    return []


def hw_update(hw, blob):
    save_functions = []
    for attr, value in blob:
        if attr == 'keyvalue_set':
            save_functions += import_kv(hw, value)
        else:
            setattr(hw, attr, value)

    return [(3, lambda: hw.save())] + save_functions


def sreg_update(sreg, blob):
    save_functions = []
    for attr, value in blob:
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
        else:
            setattr(sreg, attr, value)

    return [(2, lambda: sreg.save())] + save_functions


def system_update(system, blob):
    save_functions = []
    for attr, value in blob.iteritems():
        if attr == 'static_reg_set':
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

    return [(1, lambda: system.save())] + save_functions


def set_field(obj, attr, value):
    if hasattr(obj.__class__, attr):
        m_attr = getattr(obj.__class__, attr)
        if isinstance(m_attr.field, ForeignKey):
            m_value = m_attr.field.rel.to.objects.get(pk=value)
        else:
            raise Exception("Really bad error")
    else:
        m_value = value
    setattr(obj, attr, m_value)
