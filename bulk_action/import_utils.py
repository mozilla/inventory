from django.db.models.fields.related import ForeignKey

from systems.models import System
from core.registration.static.models import StaticReg
from core.hwadapter.models import HWAdapter

from mozdns.cname.models import CNAME
from mozdns.utils import ensure_label_domain

import decimal
import datetime
import simplejson as json


# Objects are created/updated at during different phases. The need for this
# comes from the necessity of certain objects existing before other objects
# exist. For example, a KeyValue pair needs its object to exist before it can
# be saved. Also, SREG objects need system objects before they are saved --
# likewise HWAdapter objects need SREG objects.

# As functions are built up to save a JSON blob they are paired with a PHASE
# number to ensure an order that will allow things to work.

PHASE_1 = 1
PHASE_2 = 2
PHASE_3 = 3
PHASE_4 = 4


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
        elif isinstance(o, datetime.datetime):
            return o.strftime("%Y-%m-%d %H:%M")
        elif isinstance(o, datetime.date):
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
        if isinstance(value, dict) and attr != 'views':
            # the views attr should never be touched.
            for sub_blob in value.values():
                recurse_confirm_no_pk(sub_blob)
        elif attr == 'pk':
            raise BadImportData(
                bad_blob=blob,
                msg='This object is new (it has no pk) but other objects tied '
                'to it have pk values. This is not allowed.'
            )


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
        recurse_confirm_no_pk(blob)
        system = System()
        return system_update(system, blob)


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
        recurse_confirm_no_pk(blob)
        sreg = StaticReg(system=system)
        return sreg_update(sreg, blob)


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
        recurse_confirm_no_pk(blob)
        hw = HWAdapter(sreg=sreg)
        return hw_update(hw, blob)


def import_kv(obj, blobs):
    save_functions = []
    Klass = obj.keyvalue_set.model
    for blob in blobs.values():
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


def import_cname(sreg, blobs):
    if not isinstance(blobs, list):
        raise BadImportData(
            bad_blob=blobs,
            msg='The cname attribute should be a list of CNAME blobs'
        )
    save_functions = []
    for blob in blobs:
        if 'pk' in blob:
            try:
                cname = CNAME.objects.get(pk=blob['pk'])
                save_functions += cname_update(cname, blob)
            except CNAME.DoesNotExist:
                raise BadImportData(
                    bad_blob=blob,
                    msg='Could not find the CNAME with primary key '
                    '{0}.'.format(blob['pk'])
                )
        else:
            recurse_confirm_no_pk(blob)
            save_functions += cname_update(CNAME(), blob)
    return save_functions


def cname_update(cname, blob):
    save_functions = []
    for attr, value in blob.iteritems():
        if attr == 'views':
            continue  # We handle views in save since new objects need a pk
        else:
            setattr(cname, attr, value)

    def save():
        # This code runs in a transaction that is rolled back if an exception
        # is raised.
        cname.label, cname.domain = ensure_label_domain(cname.fqdn)
        make_save(cname, blob)()
        # Now save the views
        for view in blob.get('views', []):
            cname.views.add(view)

    return [(PHASE_3, save)] + save_functions


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

    return [(PHASE_4, save)]


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

    return [(PHASE_3, save)] + save_functions


def sreg_update(sreg, blob):
    save_functions = []
    for attr, value in blob.iteritems():
        if attr == 'hwadapter_set':
            if not isinstance(value, dict):
                raise BadImportData(
                    bad_blob=blob,
                    msg='The Static Registration attribute hwadapter_set must '
                    'a dict of Hardware Adapter JSON blobs'
                )
            for hw_blob in value.values():
                save_functions += hw_import(sreg, hw_blob)
        elif attr == 'keyvalue_set':
            save_functions += import_kv(sreg, value)
        elif attr == 'cname':
            save_functions += import_cname(sreg, value)
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
        for view in blob.get('views', []):
            sreg.views.add(view)

    return [(PHASE_2, save)] + save_functions


def clone_system_extras(system, other_hostname):
    # XXX if ever SystemChangeLog is swapped out this function will need to be
    # changed
    """
    Copy all SystemChangeLog over from the system named "other_hostname" to
    system's SystemChangeLog store.

    This function is called after the system's save() is called, so if the
    object is new we will need to refresh the object before using it.
    """
    other_system = System.objects.get(hostname=other_hostname)

    def _clone_system_extras():
        s = System.objects.get(pk=system.pk)
        for cl in other_system.systemchangelog_set.all():
            cl.pk = None
            cl.system = s
            cl.save()

        # if the new system didn't have a created_on date it was set to
        # now()-ish. Set the new system's created_on to also be None
        if not other_system.created_on:
            s.created_on = None
            s.save()

    return _clone_system_extras


def system_update(system, blob):
    """
    If there is a key 'clone' with "truish" value we must look for that and
    possibly copy history from an existing object. The history will be taken
    from the system who's "hostname" is the value of the "clone" key. If no
    system exists for cloning a BadImportData exception will be raised.
    """
    save_functions = []

    mother_hostname = blob.get('clone', None)

    if mother_hostname and isinstance(mother_hostname, str):
        try:
            save_functions += [
                (PHASE_2, clone_system_extras(system, mother_hostname))
            ]
        except System.DoesNotExist:
            raise BadImportData(
                bad_blob=blob,
                msg="Tried to clone the host {0} but a host with that "
                "hostname didn't exist".format(mother_hostname)
            )

    for attr, value in blob.iteritems():
        if attr == 'staticreg_set':
            if not isinstance(value, dict):
                raise BadImportData(
                    bad_blob=blob,
                    msg='The system attribute statirc_reg_set must a dict of '
                    'Static Registration JSON blobs'
                )
            for sreg_blob in value.values():
                save_functions += sreg_import(system, sreg_blob)
        elif attr == 'keyvalue_set':
            save_functions += import_kv(system, value)
        else:
            set_field(system, attr, value)

    return [(PHASE_1, make_save(system, blob))] + save_functions


def set_field(obj, attr, value):
    # yay side effects
    if attr == 'pk':  # Don't ever set a primary key
        return

    if hasattr(obj.__class__, attr):
        m_attr = getattr(obj.__class__, attr)
        if isinstance(m_attr.field, ForeignKey):
            if value is None:
                m_value = value
            else:
                try:
                    m_value = m_attr.field.rel.to.objects.get(pk=value)
                except (ValueError, m_attr.field.rel.to.DoesNotExist), e:
                    raise BadImportData(
                        "Using the data '{0}' to look up '{1}' and "
                        "received the error '{2}'".format(value, attr, str(e))
                    )
        else:
            raise Exception("Really bad error")
    else:
        m_value = value
    setattr(obj, attr, m_value)
