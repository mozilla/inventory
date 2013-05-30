from django.test import TransactionTestCase
from django.test.client import Client
from django.core.exceptions import ValidationError

from core.registration.static.models import StaticReg
from core.group.models import Group
from core.hwadapter.models import HWAdapter
from systems.models import System
from mozdns.domain.models import Domain
from mozdns.view.models import View
from mozdns.tests.utils import create_fake_zone

import simplejson as json


class StaticRegViewTests(TransactionTestCase):
    def setUp(self):
        View.objects.create(name="public")
        View.objects.create(name="private")
        self.d = create_fake_zone('foo.com', suffix="")
        self.rd = create_fake_zone('10.in-addr.arpa', suffix="")
        self.client = Client()
        self.s = System.objects.create(hostname='exists.mozilla.com')
        self.g = Group.objects.create(name='foogroup')

    def test_create_with_no_hwadapters(self):
        # Get test data by snooping request.POST in the sreg creation view
        test_data = json.loads("""{{
            "hwadapters-TOTAL_FORMS": ["1"],
            "hwadapters-MAX_NUM_FORMS": [""],
            "hwadapters-INITIAL_FORMS": ["0"],
            "sreg-views": ["2"],
            "sreg-fqdn": ["test1.foo.com"],
            "sreg-ip_str": ["10.8.0.3"],
            "kv-sreg-name": ["foobar"],
            "override-fqdn": ["on"],
            "sreg-system": ["{system_pk}"]}}
        """.format(system_pk=self.s.pk))
        count_before = StaticReg.objects.all().count()
        resp = self.client.post(
            '/en-US/core/registration/static/create/', test_data
        )
        self.assertEqual(200, resp.status_code)
        count_after = StaticReg.objects.all().count()
        self.assertEqual(count_before + 1, count_after)
        sreg = StaticReg.objects.get(fqdn='test1.foo.com')
        self.assertEqual(1, sreg.views.all().count())
        self.assertEqual('10.8.0.3', sreg.ip_str)
        self.assertEqual(1, sreg.keyvalue_set.all().count())
        kv = sreg.keyvalue_set.all()[0]
        self.assertEqual('name', kv.key)
        self.assertEqual('foobar', kv.value)

    def test_create_with_multiple_hwadapters(self):
        # Notice how TOTAL_FORMS is 5? Django requires that the number of
        # TOTAL_FORMS to be greater than or equal to the highest number found
        # in the formset's prefix list. So in this case the highest number is 3
        # since 'hwadapters-3-' is the highest prefix. If TOTAL_FORMS is below
        # the actual form count some forms will note be processed. Django
        # allows missing forms by default.
        test_data = json.loads("""{{
            "hwadapters-TOTAL_FORMS": ["5"],
            "hwadapters-MAX_NUM_FORMS": [""],
            "hwadapters-INITIAL_FORMS": ["0"],
            "sreg-views": ["2"],
            "sreg-fqdn": ["test2.foo.com"],
            "sreg-ip_str": ["10.8.0.3"],
            "override-fqdn": ["on"],
            "sreg-system": ["{system_pk}"],
            "hwadapters-0-group": [],
            "hwadapters-0-name": ["nic0"],
            "hwadapters-0-mac": ["11:22:33:44:55:66"],
            "kv-hwadapters-0-hostname": ["valid.mozilla.com"],
            "hwadapters-1-group": [],
            "hwadapters-1-name": ["nic1"],
            "hwadapters-1-mac": ["12:22:33:44:55:66"],
            "kv-hwadapters-1-hostname": ["valid.mozilla.com"],
            "hwadapters-3-group": [],
            "hwadapters-3-name": ["nic2"],
            "hwadapters-3-mac": ["13:22:33:44:55:66"],
            "kv-hwadapters-3-hostname": ["valid.mozilla.com"]}}
        """.format(system_pk=self.s.pk, group_pk=self.g.pk))
        sreg_count_before = StaticReg.objects.all().count()
        resp = self.client.post(
            '/en-US/core/registration/static/create/', test_data
        )
        # Check the sreg
        self.assertEqual(200, resp.status_code)
        sreg_count_after = StaticReg.objects.all().count()
        self.assertEqual(sreg_count_before + 1, sreg_count_after)
        sreg = StaticReg.objects.get(fqdn='test2.foo.com')
        self.assertEqual(1, sreg.views.all().count())
        self.assertEqual('10.8.0.3', sreg.ip_str)
        self.assertEqual(0, sreg.keyvalue_set.all().count())

        # check that three adapters were created
        self.assertEqual(3, sreg.hwadapter_set.all().count())

    def test_create_with_one_hwadapter(self):
        test_data = json.loads("""{{
            "hwadapters-TOTAL_FORMS": ["1"],
            "hwadapters-MAX_NUM_FORMS": [""],
            "hwadapters-INITIAL_FORMS": ["0"],
            "sreg-views": ["2"],
            "sreg-fqdn": ["test2.foo.com"],
            "sreg-ip_str": ["10.8.0.3"],
            "override-fqdn": ["on"],
            "sreg-system": ["{system_pk}"],
            "hwadapters-0-group": ["{group_pk}"],
            "hwadapters-0-name": ["nic0"],
            "hwadapters-0-mac": ["11:22:33:44:55:66"],
            "kv-hwadapters-0-hostname": ["valid.mozilla.com"]}}
        """.format(system_pk=self.s.pk, group_pk=self.g.pk))
        count_before = StaticReg.objects.all().count()
        resp = self.client.post(
            '/en-US/core/registration/static/create/', test_data
        )
        # Check the sreg
        self.assertEqual(200, resp.status_code)
        count_after = StaticReg.objects.all().count()
        self.assertEqual(count_before + 1, count_after)
        sreg = StaticReg.objects.get(fqdn='test2.foo.com')
        self.assertEqual(1, sreg.views.all().count())
        self.assertEqual('10.8.0.3', sreg.ip_str)
        self.assertEqual(0, sreg.keyvalue_set.all().count())

        # check the hwadapter
        self.assertEqual(1, sreg.hwadapter_set.all().count())
        hw = sreg.hwadapter_set.all()[0]
        self.assertEqual(self.g, hw.group)
        self.assertEqual('11:22:33:44:55:66', hw.mac)
        self.assertEqual('nic0', hw.name)

        # check the hwadapter keyvalue store
        self.assertEqual(1, hw.keyvalue_set.all().count())
        kv = hw.keyvalue_set.all()[0]
        self.assertEqual('hostname', kv.key)
        self.assertEqual('valid.mozilla.com', kv.value)

    def test_create_invalid_sreg(self):
        test_data = json.loads("""{
            "hwadapters-TOTAL_FORMS": ["1"],
            "hwadapters-MAX_NUM_FORMS": [""],
            "hwadapters-INITIAL_FORMS": ["0"],
            "sreg-views": ["2"],
            "sreg-fqdn": ["this.machine.dont.exist.mozilla.com"],
            "sreg-ip_str": ["10.8.101.217"],
            "kv-sreg-name": ["foo"],
            "override-fqdn": ["on"],
            "sreg-system": ["6112"],
            "hwadapters-0-group": ["1"],
            "hwadapters-0-name": ["nic0"],
            "hwadapters-0-mac": ["11:22:33:44:55:66"],
            "kv-hwadapters-0-hostname": ["valid.mozilla.com"]}
        """)

        sreg_count_before = StaticReg.objects.all().count()
        hw_count_before = HWAdapter.objects.all().count()

        resp = self.client.post(
            '/en-US/core/registration/static/create/', test_data
        )
        self.assertEqual(200, resp.status_code)

        sreg_count_after = StaticReg.objects.all().count()
        hw_count_after = HWAdapter.objects.all().count()

        # Check that the sreg wasn't created
        self.assertEqual(sreg_count_before, sreg_count_after)
        # Check that the hwadapter wasn't created
        self.assertEqual(hw_count_before, hw_count_after)

    def test_create_invalid_hwadapter(self):
        test_data = json.loads("""{{
            "hwadapters-TOTAL_FORMS": ["1"],
            "hwadapters-MAX_NUM_FORMS": [""],
            "hwadapters-INITIAL_FORMS": ["0"],
            "sreg-views": ["2"],
            "sreg-fqdn": ["test3.foo.com"],
            "sreg-ip_str": ["10.8.0.3"],
            "override-fqdn": ["on"],
            "sreg-system": ["{system_pk}"],
            "hwadapters-0-group": ["{group_pk}"],
            "hwadapters-0-name": ["nic0"],
            "hwadapters-0-mac": ["11:22:33:44:55:66:bogus"],
            "kv-hwadapters-0-hostname": ["valid.mozilla.com"]}}
        """.format(system_pk=self.s.pk, group_pk=self.g.pk))
        sreg_count_before = StaticReg.objects.all().count()
        hw_count_before = HWAdapter.objects.all().count()
        resp = self.client.post(
            '/en-US/core/registration/static/create/', test_data
        )
        self.assertEqual(200, resp.status_code)
        sreg_count_after = StaticReg.objects.all().count()
        hw_count_after = HWAdapter.objects.all().count()
        # Check that the sreg wasn't created
        self.assertEqual(sreg_count_before, sreg_count_after)
        # Check that the hwadapter wasn't created
        self.assertEqual(hw_count_before, hw_count_after)
