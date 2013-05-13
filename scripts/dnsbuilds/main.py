#!/usr/bin/python
import argparse
import sys
import os
import time
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                os.pardir, os.pardir)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import manage
from mozdns.mozbind.builder import DNSBuilder, BuildError
from settings.dnsbuilds import STOP_UPDATE_FILE, LAST_RUN_FILE
from core.utils import fail_mail


def main():
    parser = argparse.ArgumentParser(description='DNS Build scripts')
    parser.add_argument('--stage-only', dest='STAGE_ONLY', action='store_true',
                        default=False, help="Just build staging and don't "
                        "copy to prod. named-checkzone will still be run.")
    parser.add_argument('--clobber-stage', dest='CLOBBER_STAGE',
                        action='store_true', default=False, help="If stage "
                        "already exists delete it before running the build "
                        "script.")
    parser.add_argument('--ship-it', dest='PUSH_TO_PROD',
                        action='store_true', default=False, help="Check files "
                        "into rcs and push upstream.")
    parser.add_argument('--preserve-stage', dest='PRESERVE_STAGE',
                        action='store_true', default=False, help="Do not "
                        "remove staging area after build completes.")
    parser.add_argument('--no-build', dest='BUILD_ZONES',
                        action='store_false', default=True, help="Do not "
                        "build zone files.")
    parser.add_argument('--no-syslog', dest='LOG_SYSLOG',
                        action='store_false', default=True, help="Do not "
                        "log to syslog.")
    parser.add_argument('--debug', dest='DEBUG',
                        action='store_true', default=False, help="Print "
                        "copious amounts of text.")
    parser.add_argument('--force-checkin', dest='FORCE',
                        action='store_true', default=False, help="Ignore "
                        "all change delta thresholds, clobber stagig area, "
                        "and build even when no tasks are scheduled.")
    parser.add_argument('--force-build', dest='FORCE_BUILD',
                        action='store_true', default=False, help="Do a buil "
                        "even if no zones are requesting to be rebuilt.")
    parser.add_argument('--status', dest='STATUS',
                        action='store_true', default=False, help="Display "
                        "info about the build configuration and exit.")
    nas = parser.parse_args(sys.argv[1:])
    b = DNSBuilder(**dict(nas._get_kwargs()))

    if nas.STATUS:
        b.status()
        return
    message = "DNS Build Error. Error: '{0}'. The build was unsuccessful."

    def write_stop_update(error):
        if os.path.exists(STOP_UPDATE_FILE):
            return
        with open(STOP_UPDATE_FILE, 'w+') as fd:
            msg = ("This file was placed here because there was an error:\n"
                   "=============== ERROR MESSAGE ======================+\n")
            fd.write(msg)
            fd.write(error)
    try:
        with open(LAST_RUN_FILE, 'w+') as fd:
            fd.write(str(int(time.time())))
        b.build_dns()
    except BuildError as why:
        b.log(why, log_level='LOG_ERR')
        write_stop_update(str(why))
        fail_mail(message.format(why))
    except Exception as err:
        fail_mail(message.format(err))
        b.log(err, log_level='LOG_CRIT')
        error_msg = "{0}\n{1}".format(str(err), traceback.format_exc())
        write_stop_update(error_msg)

if __name__ == '__main__':
    main()
