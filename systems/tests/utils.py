import random
import string
import datetime

from systems.models import System, SystemType, Allocation


def random_str(length=10):
    return ''.join(
        random.choice(string.ascii_uppercase) for i in range(length)
    )


def create_fake_host(**kwargs):
    """
    This is a factory for building valid Systems. This factory should be used
    instead of calling System methods directly for making new systems made for
    testing.

    If a new field ever becomes required we can make sure it is filled in here
    instead of updating every test that creates a new System.
    """
    if 'system_type' in kwargs:
        system_type = kwargs.pop('system_type')
    else:
        type_name = random_str()
        while SystemType.objects.filter(type_name=type_name).exists():
            type_name = random_str()
        system_type, _ = SystemType.objects.get_or_create(type_name=type_name)

    if 'allocation' in kwargs:
        allocation = kwargs.pop('allocation')
    else:
        allocation_name = random_str()
        while Allocation.objects.filter(name=allocation_name).exists():
            allocation_name = random_str()
        allocation, _ = Allocation.objects.get_or_create(name=allocation_name)

    if 'serial' in kwargs:
        serial = kwargs.pop('serial')
    else:
        serial = random_str()
        while System.objects.filter(serial=serial).exists():
            type_name = random_str()

    return System.objects.create(
        allocation=allocation,
        serial=serial,
        system_type=system_type,
        warranty_start=datetime.datetime.now(),
        warranty_end=datetime.datetime.now(),
        **kwargs
    )
