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
from django.contrib.sites.models import Site
import user_systems.models as model
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from settings import SCRIPT_URL, DESKTOP_EMAIL_ADDRESS, FROM_EMAIL_ADDRESS



def main():
    text_message = ""
    html_message = ""
    loaners_due = model.UnmanagedSystem.objects.select_related().get_loaners_due()
    for loaner in loaners_due:
        text_message += "%s borrowed by %s is due %s\n" %(loaner, loaner.owner.name, loaner.loaner_return_date)
        html_message += "<tr><td><a href='%s/user_systems/show/%i/'>%s</a></td><td>%s</td><td>%s</td></tr>" %(SCRIPT_URL, loaner.id, loaner, loaner.owner.name, loaner.loaner_return_date)

    
    sender = FROM_EMAIL_ADDRESS
    receivers = [DESKTOP_EMAIL_ADDRESS]

    if len(loaners_due) > 0:
        try:
            html = '<html><head></head><body><table><tr><th>Loaner</th><th>Owner</th><th>Due</th></tr>%s</table></body></html>' % (html_message)
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Inventory Loaner Systems Due"
            part1 = MIMEText(text_message, 'plain')
            part2 = MIMEText(html, 'html')
            msg.attach(part1)
            msg.attach(part2)
            smtpObj = smtplib.SMTP('localhost')
            smtpObj.sendmail(sender, receivers, msg.as_string())
        except SMTPException:
            print "Error: unable to send email"
    




if __name__ == '__main__':
    main()
