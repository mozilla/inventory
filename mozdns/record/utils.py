import copy
import simplejson as json
from gettext import gettext as _

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.forms.util import ErrorList, ErrorDict
from django.shortcuts import render
from django.http import Http404

import reversion

from mozdns.address_record.models import AddressRecord
from mozdns.address_record.forms import AddressRecordFQDNForm
from mozdns.address_record.forms import AddressRecordForm
from mozdns.ptr.models import PTR
from mozdns.ptr.forms import PTRForm
from mozdns.srv.models import SRV
from mozdns.srv.forms import SRVForm, FQDNSRVForm
from mozdns.sshfp.models import SSHFP
from mozdns.sshfp.forms import SSHFPForm, FQDNSSHFPForm
from mozdns.txt.models import TXT
from mozdns.txt.forms import TXTForm, FQDNTXTForm
from mozdns.mx.models import MX
from mozdns.mx.forms import MXForm, FQDNMXForm
from mozdns.cname.models import CNAME
from mozdns.cname.forms import CNAMEFQDNForm, CNAMEForm
from mozdns.soa.models import SOA
from mozdns.soa.forms import SOAForm
from mozdns.domain.models import Domain
from mozdns.domain.forms import DomainForm
from mozdns.nameserver.models import Nameserver
from mozdns.nameserver.forms import NameserverForm
from mozdns.utils import ensure_label_domain, prune_tree

from core.registration.static.models import StaticReg
from core.registration.static.forms import StaticRegFQDNForm
from core.registration.static.forms import StaticRegForm


class RecordView(object):
    form_template = 'record/ajax_form.html'

    def get_context_data(self, context):
        return context

    def get(self, request, record_type, record_pk):
        if not record_pk:
            object_ = None
        else:
            try:
                object_ = self.Klass.objects.get(pk=record_pk)
            except self.Klass.DoesNotExist:
                raise Http404
        return self._display_object(request, object_, record_type, record_pk)

    def _display_object(self, request, object_, record_type, record_pk):
        if object_:
            domains = []
        else:
            domains = [domain.name for
                       domain in
                       Domain.objects.filter(is_reverse=False)]
        if not object_:
            form = self.DisplayForm()
        else:
            form = self.DisplayForm(instance=object_)
        if object_:
            delete_redirect_url = object_.get_delete_redirect_url()
        else:
            delete_redirect_url = '/core/search/'

        return render(request, self.form_template, {
            'form': form,
            'object_': object_,
            'delete_redirect_url': delete_redirect_url,
            'record_type': record_type if record_type else '',
            'record_pk': record_pk if record_pk else '',
            'domains': json.dumps(domains),
        })

    def post(self, request, record_type, record_pk):
        try:
            object_ = self.Klass.objects.get(pk=str(record_pk))
        except (ObjectDoesNotExist, ValueError):
            # We will try to create an object
            object_ = None

        new_object, errors = self.post_handler(
            object_, record_type, request.POST.copy()
        )

        if object_:
            verb = "update"
        else:
            verb = "create"
            object_ = new_object

        if errors:
            # Reload the object.
            if object_:
                object_ = self.Klass.objects.get(pk=object_.pk)
            return_form = self.DisplayForm(request.POST)
            return_form._errors = errors
            message = "Errors during {0}. Commit Aborted.".format(verb)
        else:
            message = "Succesful {0}".format(verb)
            return_form = self.DisplayForm(instance=new_object)
            record_pk = new_object.pk

        if object_:
            delete_redirect_url = object_.get_delete_redirect_url()
        else:
            delete_redirect_url = '/core/search/'

        basic_context = {
            'form': return_form,
            'message': message,
            'record_type': record_type,
            'delete_redirect_url':  delete_redirect_url,
            'record_pk': record_pk,
            'object_': object_
        }

        # Allow overrides
        context = self.get_context_data(basic_context)

        return render(request, self.form_template, context)

    def modify_qd(self, qd, object_=None):
        fqdn = qd.pop('fqdn', [''])[0]
        domain = None
        # if record_type not in ('PTR', 'NS', 'DOMAIN', 'SOA'):
        try:
            label, domain = ensure_label_domain(fqdn)
            # If something goes bad latter on you must call prune_tree on
            # domain.  If you don't do this there will be a domain leak.
        except ValidationError, e:
            errors = ErrorDict()
            errors['fqdn'] = e.messages
            return None, errors
        qd['label'], qd['domain'] = label, str(domain.pk)
        return qd, None

    def post_handler(self, object_, record_type, orig_qd):
        """Create or update object_. qd is a QueryDict."""
        qd = copy.deepcopy(
            orig_qd)  # If there are ever errors, we have to preserver
                                     # the original qd
        comment = qd.pop('comment', [''])[0].strip()

        # This little chunk of code could be factored out, but I think it's
        # more clear when you see which objects don't need to call this in one
        # spot.
        qd, errors = self.modify_qd(qd, object_=object_)
        if errors:
            return None, errors

        # Create a save-able form to create/update the object
        if object_:
            object_form = self.form(qd, instance=object_)
        else:
            object_form = self.form(qd)

        if object_form.is_valid():
            try:
                object_ = object_form.save()
                reversion.set_comment(comment)
            except ValidationError, e:
                if 'domain' in qd:
                    prune_tree(Domain.objects.get(pk=qd['domain']))
                e_dict = ErrorDict()
                e_dict['__all__'] = ErrorList(e.messages)
                return None, e_dict
            return object_, None
        else:
            if 'domain' in qd:
                prune_tree(Domain.objects.get(pk=qd['domain']))
            return None, object_form._errors


def make_rdtype_tagger(tagged_klasses):
    def tag(Klass):
        tagged_klasses[Klass.__name__.strip('_')] = Klass
        return Klass
    return tag

obj_meta = {}
tag_rdtype = make_rdtype_tagger(obj_meta)


def get_obj_meta(record_type):
    return obj_meta[record_type]

"""
Name the class the same as the rdtype it's standing for.
"""


@tag_rdtype
class A_(RecordView):
    Klass = AddressRecord
    form = AddressRecordForm
    DisplayForm = AddressRecordFQDNForm


@tag_rdtype
class AAAA_(A_):
    pass


@tag_rdtype
class SREG_(RecordView):
    form_template = 'record/sreg_ajax_form.html'
    Klass = StaticReg
    form = StaticRegForm
    DisplayForm = StaticRegFQDNForm

    def modify_qd(self, qd, object_=None):
        # We hide the system attribute in the update form so we must
        # reintroduce it into the qd when saving the object.
        if object_:
            qd['system'] = object_.system.pk
        return super(SREG_, self).modify_qd(qd, object_=object_)


@tag_rdtype
class CNAME_(RecordView):
    Klass = CNAME
    form = CNAMEForm
    DisplayForm = CNAMEFQDNForm


@tag_rdtype
class DOMAIN_(RecordView):
    Klass = Domain
    form = DomainForm
    DisplayForm = DomainForm

    def modify_qd(self, qd):
        return qd, None


@tag_rdtype
class MX_(RecordView):
    Klass = MX
    form = MXForm
    DisplayForm = FQDNMXForm


@tag_rdtype
class NS_(RecordView):
    Klass = Nameserver
    form = NameserverForm
    DisplayForm = NameserverForm

    def modify_qd(self, qd, **kwargs):
        domain_pk = qd.pop('domain', '')[0]
        try:
            domain = Domain.objects.get(pk=domain_pk)
            qd['domain'] = str(domain.pk)
        except Domain.DoesNotExist:
            error_message = _("Could not find domain with pk "
                              "'{0}'".format(domain_pk))
            errors = ErrorDict()
            errors['domain'] = [error_message]
            return None, errors
        return qd, None


@tag_rdtype
class PTR_(RecordView):
    Klass = PTR
    form = PTRForm
    DisplayForm = PTRForm

    def modify_qd(self, qd, **kwargs):
        return qd, None


@tag_rdtype
class TXT_(RecordView):
    Klass = TXT
    form = TXTForm
    DisplayForm = FQDNTXTForm


@tag_rdtype
class SSHFP_(RecordView):
    Klass = SSHFP
    form = SSHFPForm
    DisplayForm = FQDNSSHFPForm


@tag_rdtype
class SOA_(RecordView):
    Klass = SOA
    form = SOAForm
    DisplayForm = SOAForm

    def modify_qd(self, qd, **kwargs):
        return qd, None


@tag_rdtype
class SRV_(RecordView):
    Klass = SRV
    form = SRVForm
    DisplayForm = FQDNSRVForm
