# Random functions that get used in different places.
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Q, F

from mozdns.domain.models import Domain
from mozdns.mx.models import MX
from mozdns.sshfp.models import SSHFP
from mozdns.txt.models import TXT
from mozdns.srv.models import SRV
from mozdns.address_record.models import AddressRecord
from mozdns.cname.models import CNAME
from core.registration.static.models import StaticReg

from copy import deepcopy


def tablefy(objects, views=True):
    """
    Given a list of objects, build a matrix that is can be printed as a table.
    Also return the headers for that table. Populate the given url with the pk
    of the object. Return all headers, field array, and urls in a seperate
    lists.

    :param  objects: A list of objects to make the matrix out of.
    :type   objects: AddressRecords
    """
    matrix = []
    urls = []
    headers = []
    if not objects:
        return (None, None, None)
    # Build the headers
    for title, value in objects[0].details():
        headers.append(title)
    if views:
        headers.append("Views")

    # Build the matrix and urls
    for obj in objects:
        row = []
        urls.append(obj.get_absolute_url())
        for title, value in obj.details():
            row.append(value)
        if views:
            views = ""
            if hasattr(obj, 'views'):
                for view in obj.views.all():
                    views += view.name + ", "
                views = views.strip(", ")
                row.append(views)

        matrix.append(row)

    return (headers, matrix, urls)


# TODO depricate this
def slim_form(domain_pk=None, form=None):
    """
    What is going on? We want only one domain showing up in the
    choices.  We are replacing the query set with just one object. Ther
    are two querysets. I'm not really sure what the first one does, but
    I know the second one (the widget) removes the choices. The third
    line removes the default u'--------' choice from the drop down.
    """
    return form


def get_clobbered(domain_name):
    classes = [MX, AddressRecord, CNAME, TXT, SRV, StaticReg, SSHFP]
    clobber_querysets = []  # Objects that have the same name as a domain
    for Klass in classes:
        objs = Klass.objects.select_for_update().filter(fqdn=domain_name)
        if objs.exists():
            clobber_querysets.append(objs)
    return clobber_querysets


def ensure_domain(name, purgeable=False, inherit_soa=False, force=False):
    """This function will take ``domain_name`` and make sure that a domain with
    that name exists. If this function creates a domain it will set the
    domain's purgeable flag to the value of the named arguement ``purgeable``.
    See the doc page about Labels and Domains for other information about this
    function.

    This function will attempt to prevent you from:
        * creating a new TLD
        * creating a domain that would be a child of a delegated domain
        * creating a domain that wouldn't exist in an existing zone (it
            wouldn't have an SOA)

    You can override these constrains by setting the ``force`` named argument
    to ``True``.

    By default if a domain's parent has an SOA, the new domain will not inherit
    that SOA. You can cause the domain to inherit the SOA by passing the named
    argument ``inherit_soa`` as ``True``. For example, the function
    :func:`ensure_label_domain` passes ``inherit_soa=True``.

    If a domain already exists with a name equal to ``name`` it is immediately
    returned. It is up to the caller to ensure that ``purgeable`` is set if it
    is needed.
    """
    try:
        domain = Domain.objects.get(name=name)
        return domain
    except ObjectDoesNotExist:
        pass

    # Looks like we are creating some domains. Make sure the first domain we
    # create is under a domain that has a non-None SOA reference.
    parts = list(reversed(name.split('.')))

    if not force:
        domain_name = ''
        leaf_domain = None
        # Find the leaf domain.
        for i in range(len(parts)):
            domain_name = parts[i] + '.' + domain_name
            domain_name = domain_name.strip('.')
            try:
                tmp_domain = Domain.objects.get(name=domain_name)
                # It got here so we know we found a domain.
                leaf_domain = tmp_domain
            except ObjectDoesNotExist:
                continue

        if not leaf_domain:
            raise ValidationError(
                "Creating this record would cause the "
                "creation of a new TLD. Please contact "
                "http://www.icann.org/ for more information.")
        if leaf_domain.delegated:
            raise ValidationError(
                "Creating this record would cause the "
                "creation of a domain that would be a child of a "
                "delegated domain.")
        if not leaf_domain.soa:
            raise ValidationError(
                "Creating this record would cause the "
                "creation of a domain that would not be in an existing "
                "DNS zone.")

    domain_name = ''
    # We know the end domain doesn't exist, so we build it up incrementally
    # starting at the very right most parent domain. If we find that a parent
    # domain already exists we continue until we find the domain that doesn't
    # exist.
    for i in range(len(parts)):
        domain_name = parts[i] + '.' + domain_name
        domain_name = domain_name.strip('.')
        if Domain.objects.filter(name=domain_name).exists():
            continue

        # We are about to create a domain that previously didn't exist!
        clobber_querysets = get_clobbered(domain_name)
        # Don't use get_or_create here because we need to pass certain kwargs
        # to clean()
        domain = Domain(name=domain_name)
        # we know the clobber_querysets may conflict, but we will handle
        # resolving the conflict later in this function

        if purgeable:
            domain.purgeable = True

        domain.clean(ignore_conflicts=True)  # master domain is set here

        if (inherit_soa and domain.master_domain and
                domain.master_domain.soa is not None):
            domain.soa = domain.master_domain.soa

        # get the domain in the db so we can save the clobbered objects
        domain.save(do_full_clean=False)

        # update the objects that initially conflicted with this domain
        for qs in clobber_querysets:
            qs.update(domain=domain, label='')

        # full_clean() wasn't called on this domain but clean() was. Calling
        # clean_feilds() will ensure we have done the equivalent of a
        # full_clean() on the domain.
        domain.clean_fields()

    return domain


def ensure_label_domain(fqdn, force=False):
    """Returns a label and domain object."""
    if fqdn == '':
        raise ValidationError("FQDN cannot be the emptry string.")
    try:
        domain = Domain.objects.get(name=fqdn)
        if not domain.soa and not force:
            raise ValidationError("You must create a record inside an "
                                  "existing zones.")
        return '', domain
    except ObjectDoesNotExist:
        pass
    fqdn_partition = fqdn.split('.')
    if len(fqdn_partition) == 1:
        raise ValidationError("Creating this record would force the creation "
                              "of a new TLD '{0}'!".format(fqdn))
    else:
        label, domain_name = fqdn_partition[0], '.'.join(fqdn_partition[1:])
        domain = ensure_domain(domain_name, purgeable=True, inherit_soa=True)
        if not domain.soa and not force:
            raise ValidationError("You must create a record inside an "
                                  "existing zones.")
        return label, domain


def prune_tree(domain):
    return prune_tree_helper(domain, [])


def prune_tree_helper(domain, deleted_domains):
    if not domain:
        return deleted_domains  # We didn't delete anything
    if domain.domain_set.all().count():
        return deleted_domains  # We can't delete this domain. It has children
    if domain.has_record_set():
        return deleted_domains  # There are records for this domain
    elif not domain.purgeable:
        return deleted_domains  # This domain should not be deleted by a
                                # computer.
    else:
        master_domain = domain.master_domain
        if not master_domain:
            return deleted_domains
        purged_domain = deepcopy(domain)
        purged_domain.id = None
        deleted_domains.append(purged_domain)
        domain.delete()
        return prune_tree_helper(master_domain, deleted_domains)


def get_zones():
    """This function returns a list of domains that are at the root of their
    respective zones."""
    return Domain.objects.filter(~Q(master_domain__soa=F('soa')),
                                 soa__isnull=False)
