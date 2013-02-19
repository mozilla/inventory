#!/usr/bin/python

import sys
import os
try:
    import json
except:
    from django.utils import simplejson as json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))
import manage
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.base'

from django.test.client import Client
from systems.models import ScheduledTask
always_push_svn = True
def main():
    client = Client()
    dhcp_scopes = []
    dhcp_scopes = json.loads(client.get('/api/keyvalue/?key=is_dhcp_scope', follow=True).content)
    #print dhcp_scopes
    for dhcp_scope in dhcp_scopes:
        try:
            dhcp_scope = dhcp_scope.split(":")[1]
            ScheduledTask(task=dhcp_scope, type='dhcp').save()
        except:
            pass

if __name__ == '__main__':
    main()
