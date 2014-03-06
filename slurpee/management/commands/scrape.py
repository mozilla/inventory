import logging
import simplejson as json

from django.core.management.base import BaseCommand, CommandError

from settings.scrape import config
from slurpee.puppet_slurp import slurp_puppet_facts

from settings.scrape import ALERT_FILE


def write_alert(alert):
    with open(ALERT_FILE, 'r+') as fd:
        alerts = json.loads(fd.read().strip())
        fd.seek(0)
        alerts['slurp'] = alert
        fd.write(json.dumps(alerts))


def clear_alerts():
    with open(ALERT_FILE, 'w+') as fd:
        contents = fd.read()
        if not contents.strip():
            contents = "{}"
        alerts = json.loads(contents)
        alerts.pop('slurp', None)
        fd.write(json.dumps(alerts))


class Command(BaseCommand):
    args = '<source ...>'
    help = 'Pull in data from exterior sources'

    def handle(self, *sources, **opts):
        if 'verbosity' in opts and int(opts['verbosity']) > 1:
            logging.basicConfig(level=logging.DEBUG)

        if not sources:
            raise CommandError("I need a source to scrape")

        clear_alerts()
        for source_name, c in config.iteritems():
            if not ('all' in sources or source_name in sources):
                continue

            if 'type' not in c:
                raise CommandError(
                    "Invalid config. Couldn't find type of {0}".format(c)
                )

            if c['type'] == 'puppet-dashboard':
                try:
                    slurp_puppet_facts(
                        source=source_name, source_url=c['source-url'],
                        auth=(c['user'], c['pass']), facts=c['facts'],
                        ssl_verify=c.get('ssl-verify', True)
                    )
                except KeyError, e:
                    raise CommandError(
                        "Invalid config for {0}. {1}".format(source_name, e)
                    )
                except Exception, e:
                    write_alert(
                        "Exception type: {0}. Error: {1} ".format(
                            type(e), str(e))
                    )
                    logging.error(
                        "Halting external data import due to: "
                        "{0}".format(str(e))
                    )
                    return
