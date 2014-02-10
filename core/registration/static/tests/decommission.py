from django.test import TestCase
from django.core.exceptions import ValidationError

from core.registration.static.models import StaticReg
from systems.tests.utils import create_fake_host
from mozdns.view.models import View

from mozdns.tests.utils import create_fake_zone


class StaticRegDecommissionTests(TestCase):
    def setUp(self):
        self.s = create_fake_host(hostname='asdf.mozilla.com')
        self.domain = create_fake_zone("foobar.mozilla.com", suffix="")
        create_fake_zone("10.in-addr.arpa", suffix="")
        View.objects.get_or_create(name="private")

    def test_decommision(self):
        sreg = StaticReg.objects.create(
            label='asf', domain=self.domain, system=self.s,
            ip_type='4', ip_str='10.0.2.1'
        )
        sreg.decommissioned = True
        sreg.save()
        self.assertTrue(sreg.fqdn.startswith('[DECOMMISSIONED]'))
        self.assertTrue(sreg.ip_str != '10.0.2.1')

        sreg.full_clean()
        sreg.bind_render_record()

    def test_recommision(self):
        sreg = StaticReg.objects.create(
            label='asf', domain=self.domain, system=self.s,
            ip_type='4', ip_str='10.0.2.1'
        )
        sreg.decommissioned = True
        sreg.save()
        sreg.decommissioned = False
        self.assertRaises(ValidationError, sreg.save)
        sreg.label = 'valid'
        sreg.domain = self.domain
        self.assertRaises(ValidationError, sreg.save)
        sreg.ip_str = '10.2.3.4'
        sreg.save()
