#!/usr/bin/python
import argparse
import shutil
import shlex
import sys
import argparse
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.base'
import manage
from mozdns.mozbind.runner import DNSBuilder


def main():
    parser = argparse.ArgumentParser(description='DNS Build scripts')
    parser.add_argument('--ro', dest='RO', action='store_true',
                        default=False, help="Just try to bulid the zones. "
                        "Don't write anything to the file system.")
    nas = parser.parse_args(sys.argv[1:])
    b = DNSBuilder()
    if nas.RO:
        b.RO = True
    b.build_dns()

if __name__ == '__main__':
    main()

