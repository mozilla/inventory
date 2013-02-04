#!/usr/bin/python
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))
import manage
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.base'
from systems import models
def main():
    print 'id, old_hostname, new_hostname'
    for sys in models.System.objects.all():
        if sys.keyvalue_set.filter(key='system.hostname.alias.0'):
            old_hostname = sys.keyvalue_set.filter(key='system.hostname.alias.0')[0].value
        else:
            old_hostname = sys.hostname
        if old_hostname != sys.hostname:
            print '%s,%s,%s' % (sys.id, old_hostname, sys.hostname)

if __name__ == '__main__':
    main()
