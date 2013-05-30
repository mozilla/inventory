from tastypie.test import ResourceTestCase


from mozdns.tests.utils import create_fake_zone, random_label
from core.registration.static.models import StaticReg
from core.hwadapter.models import HWAdapter
from core.group.models import Group
from systems.models import System

import simplejson as json

API_VERSION = '1'


class TestCaseUtils(object):
    def localize_url(self, url):
        if 'en-US' not in url:
            url = url.replace('core/api', 'en-US/core/api')
        return url


class CoreAPITests(TestCaseUtils):
    object_list_url = "/en-US/core/api/v{0}_core/{1}/"
    object_url = "/en-US/core/api/v{0}_core/{1}/{2}/"

    def setUp(self):
        super(CoreAPITests, self).setUp()

    def test_create(self):
        resp, post_data = self.generic_create(self.post_data())
        new_object_url = resp['Location']
        new_resp = self.api_client.get(
            new_object_url, format='json', follow=True
        )
        self.assertValidJSONResponse(new_resp)
        new_obj_data = json.loads(new_resp.content)
        self.compare_data(post_data, new_obj_data)

    def compare_data(self, old_data, new_obj_data):
        for key in old_data.keys():
            self.assertEqual(old_data[key], new_obj_data[key])

    def test_update(self):
        # Are these test's failing? See this bug.
        # https://github.com/toastdriven/django-tastypie/issues/597
        # Please monkey patch tastypie
        # tastypie/test.py Line
        # diff --git a/tastypie/test.py b/tastypie/test.py
        # index e395158..27f813f 100644
        # --- a/tastypie/test.py
        # +++ b/tastypie/test.py
        # @@ -161,6 +161,8 @@ class TestApiClient(object):
        #
        #          if data is not None:
        # kwargs['data'] = self.serializer.serialize(data, format=content_type)
        # +            if content_type == 'application/json':
        # +                kwargs['data'] = str(kwargs['data'])
        #
        #  if authentication is not None:
        #     kwargs['HTTP_AUTHORIZATION'] = authentication

        post_data = self.post_data()
        resp, post_data = self.generic_create(post_data)
        new_object_url = resp['Location']
        patch_data = self.post_data()
        update_resp, patch_data = self.generic_update(new_object_url,
                                                      patch_data)

        # Now make sure the data used to patch is sticking to the model.
        patch_resp = self.api_client.get(
            new_object_url, format='json', follow=True
        )
        self.assertValidJSONResponse(patch_resp)
        patch_obj_data = json.loads(patch_resp.content)
        self.compare_data(patch_data, patch_obj_data)

    def test_delete(self):
        obj_count = self.test_type.objects.count()
        resp, post_data = self.generic_create(self.post_data())
        new_object_url = self.localize_url(resp['Location'])
        self.assertEqual(self.test_type.objects.count(), obj_count + 1)
        resp = self.api_client.delete(new_object_url, format='json')
        self.assertHttpAccepted(resp)
        self.assertEqual(self.test_type.objects.count(), obj_count)

    def generic_update(self, patch_url, patch_data, assertResponse=None):
        patch_url = self.localize_url(patch_url)
        obj_count = self.test_type.objects.count()
        resp = self.api_client.patch(patch_url, format='json',
                                     data=patch_data)
        if not assertResponse:
            self.assertHttpAccepted(resp)
        else:
            assertResponse(resp)
        # Verify a no new object has been added.
        self.assertEqual(self.test_type.objects.count(), obj_count)
        return resp, patch_data

    def generic_create(self, post_data, assertResponse=None, fail=False):
        # Check how many are there first.
        obj_count = self.test_type.objects.count()
        create_url = self.object_list_url.format(
            API_VERSION, str(self.test_name).lower())
        resp = self.api_client.post(create_url, format='json', data=post_data)
        if assertResponse:
            assertResponse(resp)
        else:
            self.assertHttpCreated(resp)
        # Verify a new one has been added.
        if not fail:
            self.assertEqual(self.test_type.objects.count(), obj_count + 1)
        return resp, post_data

    def test_changing_only_one_field(self):
        resp, post_data = self.generic_create(self.post_data())
        new_object_url = self.localize_url(resp['Location'])
        change_post_data = {}
        change_post_data['description'] = "==DIFFERENT=="
        post_data['description'] = "==DIFFERENT=="
        resp, patch_data = self.generic_update(
            new_object_url, change_post_data
        )
        new_resp = self.api_client.get(
            new_object_url, format='json', follow=True
        )
        updated_obj_data = json.loads(new_resp.content)
        self.compare_data(post_data, updated_obj_data)


class HWAdapterTest(CoreAPITests, ResourceTestCase):
    test_type = HWAdapter
    test_name = 'hwadapter'

    def setUp(self):
        create_fake_zone('2.ip6.arpa', suffix="")
        self.domain = create_fake_zone('foo.mozilla.com', suffix='')
        self.s = System.objects.create(hostname='foo.mozilla.com')
        self.sreg = StaticReg.objects.create(
            label='', domain=self.domain, ip_str='2222:123::', ip_type='6',
            system=self.s
        )
        self.s = System.objects.create(hostname='foobar.mozilla.com')
        self.g = Group.objects.create(name='foobar')
        super(HWAdapterTest, self).setUp()

    def compare_data(self, old_data, new_obj_data):
        for key in old_data.keys():
            if key in ('sreg', 'group'):
                continue
            self.assertEqual(old_data[key], new_obj_data[key])

    def post_data(self):
        return {
            'description': random_label(),
            'name': 'eth0',
            'sreg': self.sreg.pk
        }
