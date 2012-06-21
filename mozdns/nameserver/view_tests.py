from django.test import TestCase
from django.test.client import Client

from mozdns.domain.models import Domain
from mozdns.nameserver.models import Nameserver
from mozdns.tests.view_tests import GenericViewTests, random_label
from settings import MOZDNS_BASE_URL



class NSViewTests(TestCase):
    def setUp(self):
        url_slug = "nameserver"
        dname = random_label()
        self.client = Client()
        self.url_slug = url_slug
        self.domain, create = Domain.objects.get_or_create(name=dname)
        while not create:
            dname = "a"+dname
            self.domain, create = Domain.objects.get_or_create(name=dname)
        server = random_label()
        self.test_obj, create = Nameserver.objects.get_or_create( server=server, domain= self.domain )
        while not create:
            server = "a"+server
            self.test_obj, create = Nameserver.objects.get_or_create( server=server, domain= self.domain )

    def post_data(self):
        server = random_label()
        return {'server': server, 'domain':self.domain.pk}


builder = GenericViewTests()
for test in builder.build_all_tests():
    setattr(NSViewTests,test.__name__+"_ns", test)
