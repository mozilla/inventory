#!/usr/bin/env python
import sys
import simplejson as json

NAGIOS_FILE = "./nagios_alerts.json"

OKAY = 0
WARNING = 1
CRITICAL = 2


def main():
    try:
        with open(NAGIOS_FILE, 'r') as fd:
            contents = fd.read().strip()
            if not contents:
                print "Empty nagios status file at {0}".format(NAGIOS_FILE)
                return WARNING

            try:
                alerts = json.loads(contents)
            except ValueError:
                print "Malformed JSON in nagios status file at {0}".format(
                    NAGIOS_FILE)
                return WARNING

            if not alerts:
                print "All is well"
                return OKAY

            for alert, msg in alerts.iteritems():
                print "{0}: {1} ".format(alert, msg)
            return CRITICAL
    except IOError:
        print "Misconfigured alert. Couldn't find {0}".format(NAGIOS_FILE)
        return WARNING


if __name__ == '__main__':
    sys.exit(main())
