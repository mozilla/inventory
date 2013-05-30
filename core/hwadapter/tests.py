from django.test import TestCase

from core.registration.static.models import StaticReg
from core.hwadapter.models import HWAdapter
from systems.models import System
from mozdns.tests.utils import create_fake_zone


class HWAdapterTests(TestCase):
    def setUp(self):
        create_fake_zone('10.in-addr.arpa', suffix='')
        self.domain = create_fake_zone('foo.mozilla.com', suffix='')
        self.s = System.objects.create(hostname='foo.mozilla.com')
        self.sreg = StaticReg.objects.create(
            label='', domain=self.domain, ip_str='10.0.0.1', ip_type='4',
            system=self.s
        )

    def test_create(self):
        h = HWAdapter.objects.create(
            mac='11:22:33:44:55:66', sreg=self.sreg, name='foo'
        )
        repr(h)
