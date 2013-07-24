__import__('inventory_context')
from systems.models import System

for s in System.objects.all():
    if s.hostname.endswith(' ') or s.hostname.startswith(' '):
        print "Bad hostname was '{0}'".format(s.hostname)
        print "fixing"
        s.hostname = s.hostname.strip()
        s.save()
