#!/usr/bin/python

try:
    import json
except:
    from django.utils import simplejson as json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.base'
import manage
import smtplib
import user_systems.models as model
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from settings import SCRIPT_URL, FROM_EMAIL_ADDRESS



def main():
    owners = model.Owner.objects.filter(email__gt='')
    sender = FROM_EMAIL_ADDRESS
    for owner in owners:
        owner_systems = owner.unmanagedsystem_set
        print owner_systems.count()
        if owner_systems.count() > 0:
            text_message = "You have the following systems assigned to you\n"
            html_message = ""
            owner_email = owner.email
            for system in owner_systems.all():
                print "%s %s" % (owner_email, system)
                text_message += "%s\n" %(system)
                html_message += "<tr><td><a href='%s/user_systems/show/%i/'>%s</a></td><td>%s</td></tr>" %(SCRIPT_URL, system.id, system, owner)
            ## Send email here
            receivers = [owner.email]
            html = '<html><head></head><body><table><tr><th>Loaner</th><th>Owner</th></tr>%s</table></body></html>' % (html_message)
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Your Inventory System Report"
            part1 = MIMEText(text_message, 'plain')
            part2 = MIMEText(html, 'html')
            msg.attach(part1)
            msg.attach(part2)
            smtpObj = smtplib.SMTP('localhost')
            smtpObj.sendmail(sender, receivers, msg.as_string())

if __name__ == '__main__':
    main()
