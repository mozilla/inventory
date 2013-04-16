import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                os.pardir, os.pardir)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import manage

from csv.importer import main


if __name__ == "__main__":
    main(sys.argv[1])
