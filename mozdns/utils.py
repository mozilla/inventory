# Random functions that get used in different places.
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from mozdns.domain.models import Domain
from mozdns.mx.models import MX
from mozdns.txt.models import TXT
from mozdns.srv.models import SRV
from mozdns.address_record.models import AddressRecord
from mozdns.cname.models import CNAME
from mozdns.view.models import View
from core.interface.static_intr.models import StaticInterface

from copy import deepcopy
import pdb


def tablefy(objects, views=True):
    """Given a list of objects, build a matrix that is can be printed as a
    table. Also return the headers for that table. Populate the given url with
    the pk of the object. Return all headers, field array, and urls in a
    seperate lists.

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


def slim_form(domain_pk=None, form=None):
    """ What is going on? We want only one domain showing up in the
    choices.  We are replacing the query set with just one object. Ther
    are two querysets. I'm not really sure what the first one does, but
    I know the second one (the widget) removes the choices. The third
    line removes the default u'--------' choice from the drop down.  """
    if not form:
        raise Http404
    if domain_pk:
        query_set = Domain.objects.filter(id=domain_pk)
        if not query_set:
            raise Http404
        if not form.fields.get('domain', False):
            raise Http404
        form.fields['domain']._queryset = query_set
        form.fields['domain'].widget.choices.queryset = query_set
        form.fields['domain'].empty_label = None
    return form

def get_clobbered(domain_name):
    classes = [MX, AddressRecord, CNAME, TXT, SRV, StaticInterface]
    clobber_objects = []  # Objects that have the same name as a domain
    for Klass in classes:
        objs = Klass.objects.filter(fqdn=domain_name)
        for obj in objs:
            obj_views = [view.name for view in obj.views.all()]
            new_obj = deepcopy(obj)
            new_obj.id = None
            new_obj.label = ""
            clobber_objects.append((new_obj, obj_views))
            if Klass == AddressRecord:
                kwargs = {"check_cname": False}
            else:
                kwargs = {}
            obj.delete(**kwargs)
    return clobber_objects

def ensure_domain(name, inherit_soa=False):
    try:
        domain = Domain.objects.get(name=name)
        return domain
    except ObjectDoesNotExist, e:
        pass
    parts = list(reversed(name.split('.')))
    domain_name = ''
    for i in range(len(parts)):
        domain_name = parts[i] + '.' + domain_name
        domain_name = domain_name.strip('.')
        clobber_objects = get_clobbered(domain_name)
        # need to be deleted and then recreated
        domain, created = Domain.objects.get_or_create(name=domain_name)
        if inherit_soa and created and domain.master_domain.soa is not None:
            domain.soa = domain.master_domain.soa
            domain.save()
        for object_, views in clobber_objects:
            try:
                object_.domain = domain
                object_.clean()
                object_.save()
                for view_name in views:
                    view = View.objects.get(name=view_name)
                    object_.views.add(view)
                    object_.save()
            except ValidationError, e:
                # this is bad
                pdb.set_trace()
                pass
    return domain
