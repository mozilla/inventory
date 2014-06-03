__import__('inventory_context')

import argparse

from django.db.transaction import commit_manually
from django.db import transaction

from mozdns.domain.models import Domain
from mozdns.nameserver.models import Nameserver
from mozdns.view.models import View

AKAMAI_NSS = [
    'ns1-240.akam.net',
    'ns4-64.akam.net',
    'ns7-66.akam.net',
    'ns5-65.akam.net',
]


def convert_to_akamai(domain, views=[], delete_old_nss=True):
    # Raise views to actual orm objects
    views = map(get_view, views)

    # look at existing views (excluding akamai nameservers) and remove them
    # from the views we are addressing
    for ns in domain.nameserver_set.all():
        if ns.server in AKAMAI_NSS:
            continue
        for view in views:
            print "Removing view '{0}' from '{1}'".format(view.name, ns)
            ns.views.remove(view)
        ns.save()

    # delete views that no longer belong to any views
    if delete_old_nss:
        for ns in domain.nameserver_set.all():
            if not ns.views.exists():
                print (
                    "The nameserver '{0}' had no more views. "
                    "Deleting it.".format(ns)
                )
                ns.delete()

    for server in AKAMAI_NSS:
        ns, created = Nameserver.objects.get_or_create(
            server=server, domain=domain
        )
        if created:
            print "Created: {0}".format(ns)
        for view in views:
            print "Adding '{0}' to '{1}' view".format(ns, view.name)
            ns.views.add(view)


def get_view(view_name):
    return View.objects.get(name=view_name)


def get_domain(name):
    return Domain.objects.get(name=name)


def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument(
        'domain', help='The domain to be migrated'
    )
    parser.add_argument(
        '--convert-private', dest='convert_private', default=False,
        action='store_true',
        help='Make the private view utilize akamai nameservers'
    )
    parser.add_argument(
        '--convert-public', dest='convert_public', default=False,
        action='store_true',
        help='Make the public view utilize akamai nameservers'
    )
    parser.add_argument(
        '--no-delete-old', dest='delete', default=True, action='store_false',
        help="Don't delete a namerserver that isn't in any view"
    )
    parser.add_argument(
        '--no-commit', dest='commit', default=True,
        action='store_false',
        help="Don't commit anything to the database"
    )

    nas = parser.parse_args()

    domain = get_domain(nas.domain)
    views = []

    if nas.convert_public:
        views.append('public')
    if nas.convert_private:
        views.append('private')

    @commit_manually()
    def convert():
        try:
            convert_to_akamai(
                domain, views=views, delete_old_nss=nas.delete
            )
        except:
            transaction.rollback()
            return

        if not nas.commit:
            transaction.rollback()

        transaction.commit()

    convert()

if __name__ == '__main__':
    main()
