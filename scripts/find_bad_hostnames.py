__import__('inventory_context')
from django.core.exceptions import ValidationError
from systems.models import System

for s in System.objects.all():
    try:
        s.full_clean()
    except ValidationError:
        print "Bad hostname was '{0}'".format(s.hostname)
        print "https://inventory.mozilla.org/en-US{0}".format(
            s.get_absolute_url())
        print ""
