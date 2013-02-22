from gettext import gettext as gt
from tastypie.test import ResourceTestCase

from systems.models import System
from core.interface.static_intr.models import StaticInterface
from mozdns.cname.models import CNAME
from mozdns.address_record.models import AddressRecord
from mozdns.domain.models import Domain
from mozdns.mx.models import MX
from mozdns.ptr.models import PTR
from mozdns.nameserver.models import Nameserver
from mozdns.srv.models import SRV
from mozdns.txt.models import TXT
from mozdns.sshfp.models import SSHFP
from mozdns.view.models import View
from mozdns.tests.utils import create_fake_zone, random_label, random_byte

import simplejson as json

API_VERSION = '1'

class TestCaseUtils(object):
    def localize_url(self, url):
        if 'en-US' not in url:
            url = url.replace('mozdns', 'en-US/mozdns')
        return url


class NoNameserverViewTests(object):
    def get_domain_and_post_data(self):
        # This is different for classes that have ips instead of fqdns
        domain_name = "{0}.{1}.{2}.{3}.com".format(
            random_label(), random_label(), random_label(), random_label()
        )
        root_domain = create_fake_zone(domain_name, suffix="")
        post_data = self.post_data()
        # Get the '_' in SRV records
        post_data['fqdn'] = post_data['fqdn'][0] + "asdf.asdf." + domain_name
        return root_domain, post_data

    def test_no_ns_views(self, data_source=None):
        if data_source:
            root_domain, post_data = data_source()
        else:
            root_domain, post_data = self.get_domain_and_post_data()
        self.assertEqual(1, root_domain.nameserver_set.all().count())
        ns = root_domain.nameserver_set.all()[0]
        # Remove all views from the zone
        ns.views.remove(self.public_view)
        ns.views.remove(self.private_view)

        # Creation should error and we shouldn't see a difference in the number
        # of objects in the db
        before_count = self.test_type.objects.all().count()
        post_data['views'] = ['public']
        resp, post_data = self.generic_create(
            post_data, assertResponse=self.assertHttpBadRequest, fail=True
        )
        after_count = self.test_type.objects.all().count()
        self.assertEqual(before_count, after_count)
        del post_data['views']

        ns.views.add(self.public_view)
        ns.views.add(self.private_view)

        # Re add all the views and test other things
        self.assertTrue(self.private_view in ns.views.all())
        self.assertTrue(self.public_view in ns.views.all())

        resp, post_data = self.generic_create(post_data)
        obj_data = json.loads(resp.content)
        new_object_url = resp['Location']

        # We now have a zone with a record in it. The namserver at the root of
        # the zone is in both views.

        # Remove one view and make sure putting the record in that view causes
        # a 400
        ns.views.remove(self.private_view)
        patch_data = {'pk': obj_data['pk'], 'views': ['private']}
        update_resp, patch_data = self.generic_update(
            new_object_url, patch_data,
            assertResponse=self.assertHttpBadRequest
        )

        # This shouldn't be an error
        patch_data = {'pk': obj_data['pk'], 'views': ['no-private']}
        update_resp, patch_data = self.generic_update(
            new_object_url, patch_data
        )

        # Adding to the public view should be fine because the NS is in that
        # view
        patch_data = {'pk': obj_data['pk'], 'views': ['public']}
        update_resp, patch_data = self.generic_update(
            new_object_url, patch_data
        )


class MozdnsAPITests(NoNameserverViewTests, TestCaseUtils):
    object_list_url = "/en-US/mozdns/api/v{0}_dns/{1}/"
    object_url = "/en-US/mozdns/api/v{0}_dns/{1}/{2}/"

    def setUp(self):
        super(MozdnsAPITests, self).setUp()
        self.domain = create_fake_zone(self.__class__.__name__.lower())
        self.public_view = View.objects.get_or_create(name='public')[0]
        self.private_view = View.objects.get_or_create(name='private')[0]

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
            API_VERSION, str(self.test_type.__name__).lower())
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
        new_object_url = resp['Location']
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

    def test_views(self):
        post_data = self.post_data()
        post_data['views'] = ['public']
        obj_count = self.test_type.objects.count()
        create_url = self.object_list_url.format(
            API_VERSION, str(self.test_type.__name__).lower())
        resp = self.api_client.post(create_url, format='json', data=post_data)
        self.assertHttpCreated(resp)
        self.assertEqual(self.test_type.objects.count(), obj_count + 1)
        # Get the object and check it's views
        new_object_url = resp['Location']
        new_resp = self.api_client.get(
            new_object_url, format='json', follow=True
        )
        self.assertValidJSONResponse(new_resp)
        new_obj_data = json.loads(new_resp.content)
        self.assertTrue('views' in new_obj_data)
        self.assertEqual(new_obj_data['views'], ['public'])
        # Update to both views
        views = ['public', 'private']
        post_data = {'views': views}
        obj_count = self.test_type.objects.count()
        resp, patch_data = self.generic_update(new_object_url, post_data)
        self.assertEqual(self.test_type.objects.count(), obj_count)
        self.assertTrue('views' in new_obj_data)
        new_resp = self.api_client.get(
            new_object_url, format='json', follow=True
        )
        updated_obj_data = json.loads(new_resp.content)
        for view_name in updated_obj_data['views']:
            self.assertTrue(view_name in views)

        # Now try deleteing a view.
        views = ['private']
        post_data = {'views': ['no-public']}  # This should delete public
        obj_count = self.test_type.objects.count()
        resp, patch_data = self.generic_update(new_object_url, post_data)
        self.assertEqual(self.test_type.objects.count(), obj_count)
        self.assertTrue('views' in new_obj_data)
        new_resp = self.api_client.get(
            new_object_url, format='json', follow=True
        )
        updated_obj_data = json.loads(new_resp.content)
        for view_name in updated_obj_data['views']:
            self.assertTrue(view_name in views)


class MangleTests(ResourceTestCase, TestCaseUtils):
    test_type = CNAME
    object_list_url = "/en-US/mozdns/api/v{0}_dns/{1}/"
    object_url = "/en-US/mozdns/api/v{0}_dns/{1}/{2}/"

    def setUp(self):
        super(MangleTests, self).setUp()
        self.domain = create_fake_zone(self.__class__.__name__.lower())
        View.objects.get_or_create(name='public')
        View.objects.get_or_create(name='private')

    def test_missing_key(self):
        post_data = self.post_data()
        post_data.pop('fqdn')
        obj_count = self.test_type.objects.count()
        create_url = self.object_list_url.format(
            API_VERSION, str(self.test_type.__name__).lower()
        )
        create_url = self.localize_url(create_url)
        resp = self.api_client.post(create_url, format='json', data=post_data)
        self.assertHttpBadRequest(resp)
        self.assertEqual(self.test_type.objects.count(), obj_count)

    def test_mangled_key(self):
        post_data = self.post_data()
        post_data['fqdn'] = post_data['fqdn'] + '.'
        obj_count = self.test_type.objects.count()
        create_url = self.object_list_url.format(
            API_VERSION, str(self.test_type.__name__).lower()
        )
        create_url = self.localize_url(create_url)
        resp = self.api_client.post(create_url, format='json', data=post_data)
        self.assertHttpBadRequest(resp)
        self.assertEqual(self.test_type.objects.count(), obj_count)

    def test_bad_fqdn(self):
        post_data = self.post_data()
        post_data['fqdn'] = ''
        obj_count = self.test_type.objects.count()
        create_url = self.object_list_url.format(
            API_VERSION, str(self.test_type.__name__).lower()
        )
        create_url = self.localize_url(create_url)
        resp = self.api_client.post(create_url, format='json', data=post_data)
        self.assertHttpBadRequest(resp)
        self.assertEqual(self.test_type.objects.count(), obj_count)

    def test_ensure_label_domain_fail(self):
        # MAke ensure_label_domain fail
        post_data = self.post_data()
        Domain.objects.get_or_create(name="asdf")
        Domain.objects.get_or_create(name="foo.asdf")
        domain, _ = Domain.objects.get_or_create(name="bar.foo.asdf")
        post_data['fqdn'] = 'secondbar.x.y.' + domain.name
        obj_count = self.test_type.objects.count()
        create_url = self.object_list_url.format(
            API_VERSION, str(self.test_type.__name__).lower()
        )
        create_url = self.localize_url(create_url)
        resp = self.api_client.post(create_url, format='json', data=post_data)
        self.assertHttpBadRequest(resp)
        self.assertEqual(self.test_type.objects.count(), obj_count)

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': 'b' + random_label() + "." + self.domain.name,
            'target': random_label()
        }


class DomainLeakTests(ResourceTestCase, TestCaseUtils):
    test_type = CNAME
    object_list_url = "/en-US/mozdns/api/v{0}_dns/{1}/"
    object_url = "/en-US/mozdns/api/v{0}_dns/{1}/{2}/"

    def setUp(self):
        super(DomainLeakTests, self).setUp()
        self.domain = create_fake_zone(self.__class__.__name__.lower())

    def test_leak1(self):
        # Check how many are there first.
        domain_count = Domain.objects.count()
        create_url = self.object_list_url.format(
            API_VERSION, str(self.test_type.__name__).lower()
        )
        create_url = self.localize_url(create_url)
        post_data = self.post_data()
        resp = self.api_client.post(create_url, format='json', data=post_data)
        self.assertHttpBadRequest(resp)
        # Verify a new one has been added.
        self.assertEqual(Domain.objects.count(), domain_count)
        self.assertTrue(Domain.objects.get(pk=self.domain.pk))  # paranoia
        return resp, post_data

    def post_data(self):
        return {
            # We are fucking this up on purpose.
            'fuckinup': random_label(),
            'fqdn': gt('c' + random_label() + '.' + random_label() + '.' +
                       self.domain.name),
        }


class CNAMEAPITests(MozdnsAPITests, ResourceTestCase):
    test_type = CNAME

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': 'd' + random_label() + "." + self.domain.name,
            'target': random_label()
        }


class MXAPITests(MozdnsAPITests, ResourceTestCase):
    test_type = MX

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': 'e' + random_label() + "." + self.domain.name,
            'server': random_label(),
            'priority': 123,
            'ttl': 213
        }


class SRVAPITests(MozdnsAPITests, ResourceTestCase):
    test_type = SRV

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': "_" + random_label() + "." + self.domain.name,
            'target': random_label(),
            'priority': 2,
            'weight': 2222,
            'port': 222
        }


class TXTAPITests(MozdnsAPITests, ResourceTestCase):
    test_type = TXT

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': 'f' + random_label() + "." + self.domain.name,
            'txt_data': random_label()
        }


class NameserverAPITests(MozdnsAPITests, ResourceTestCase):
    test_type = Nameserver

    def test_fqdn_create(self):
        pass

    def test_no_ns_views(self):
        root_domain = create_fake_zone("12.88.in-addr.arpa", suffix="")
        self.assertEqual(1, root_domain.nameserver_set.all().count())
        ns = root_domain.nameserver_set.all()[0]
        self.assertTrue(self.private_view in ns.views.all())
        self.assertTrue(self.public_view in ns.views.all())

        ptr = PTR(ip_str="88.12.1.1", ip_type='4', name='foo.bar')
        ptr.full_clean()
        ptr.save()

        # At this point we have a zone with a NS in both private and public
        # views. There is a ptr in the zone but its not in a view.

        # Add the ptr to the public view
        ptr.views.add(self.public_view)
        ptr = PTR.objects.get(pk=ptr.pk)
        self.assertTrue(self.public_view in ptr.views.all())

        ns_url = self.object_url.format(
            API_VERSION, str(self.test_type.__name__).lower(), ns.pk
        )  # The url for the nameserver in the zone

        # Try removing the NS from the public view, it should fail
        post_data = {'pk': ns.pk, 'views': ['no-public']}
        update_resp, post_data = self.generic_update(
            ns_url, post_data, assertResponse=self.assertHttpBadRequest
        )
        ns = Nameserver.objects.get(pk=ns.pk)
        # Nothing should have changed
        self.assertTrue(self.private_view in ns.views.all())
        self.assertTrue(self.public_view in ns.views.all())

        # We should be allowed to remove the private view
        post_data = {'pk': ns.pk, 'views': ['no-private']}
        update_resp, post_data = self.generic_update(ns_url, post_data)
        ns = Nameserver.objects.get(pk=ns.pk)
        self.assertTrue(self.private_view not in ns.views.all())
        self.assertTrue(self.public_view in ns.views.all())

        # Re add all views to the NS
        ns = Nameserver.objects.get(pk=ns.pk)
        ns.views.add(self.public_view)
        ns.views.add(self.private_view)

        # Remove the ptr from the public view and add it to the private view
        ptr.views.remove(self.public_view)
        ptr.views.add(self.private_view)

        # Try removing the NS from the private view, it should fail
        post_data = {'pk': ns.pk, 'views': ['no-private']}
        update_resp, post_data = self.generic_update(
            ns_url, post_data, assertResponse=self.assertHttpBadRequest
        )
        ns = Nameserver.objects.get(pk=ns.pk)
        self.assertTrue(self.private_view in ns.views.all())
        self.assertTrue(self.public_view in ns.views.all())

        # Create another NS record
        ns1 = Nameserver(domain=root_domain, server="foo.bar")
        ns1.save()
        ns1.views.add(self.private_view)

        # there is another NS there now, we should be able to remove the
        # private view
        post_data = {'pk': ns.pk, 'views': ['no-private']}
        update_resp, post_data = self.generic_update(ns_url, post_data)
        ns = Nameserver.objects.get(pk=ns.pk)
        self.assertTrue(self.private_view not in ns.views.all())
        self.assertTrue(self.public_view in ns.views.all())

        # The new ns (ns1) is the only ns enabled, it should not be allowed to
        # leave the private view. Try removing the NS from the private view, it
        # should fail
        post_data_ns1 = {'pk': ns1.pk, 'views': ['no-private']}
        ns1_url = self.object_url.format(
            API_VERSION, str(self.test_type.__name__).lower(), ns1.pk
        )  # The url for the nameserver in the zone
        update_resp, post_data_ns1 = self.generic_update(
            ns1_url, post_data_ns1, assertResponse=self.assertHttpBadRequest
        )
        ns1 = Nameserver.objects.get(pk=ns1.pk)
        self.assertTrue(self.private_view in ns1.views.all())
        self.assertTrue(self.public_view in ns.views.all())

        # Re-add the original ns to the private view and then delete ns1
        post_data = {'pk': ns.pk, 'views': ['private']}
        update_resp, post_data = self.generic_update(ns_url, post_data)
        ns = Nameserver.objects.get(pk=ns.pk)
        self.assertTrue(self.private_view in ns.views.all())
        self.assertTrue(self.public_view in ns.views.all())

        ns1.delete()

        # There is now one ns that is in the private and public view
        self.assertEqual(1, root_domain.nameserver_set.all().count())
        self.assertTrue(self.private_view in ns.views.all())
        self.assertTrue(self.public_view in ns.views.all())

        # We should be allowed to remove the public view
        post_data = {'pk': ns.pk, 'views': ['no-public']}
        update_resp, post_data = self.generic_update(ns_url, post_data)
        self.assertHttpAccepted(update_resp)
        ns = Nameserver.objects.get(pk=ns.pk)
        self.assertTrue(self.private_view in ns.views.all())
        self.assertTrue(self.public_view not in ns.views.all())

        # Remove the ptr from all views
        ptr.views.remove(self.private_view)
        self.assertTrue(self.public_view not in ptr.views.all())

        # We should now be able to remove the private view
        post_data = {'pk': ns.pk, 'views': ['no-private']}
        update_resp, post_data = self.generic_update(ns_url, post_data)
        ns = Nameserver.objects.get(pk=ns.pk)
        self.assertTrue(self.private_view not in ns.views.all())
        self.assertTrue(self.public_view not in ns.views.all())

    def post_data(self):
        return {
            'server': 'g' + random_label(),
            'description': random_label(),
            'ttl': random_byte(),
            'domain': self.domain.name,
        }


class SSHFPAPITests(MozdnsAPITests, ResourceTestCase):
    test_type = SSHFP

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': 'h' + random_label() + "." + self.domain.name,
            'algorithm_number': 1,
            'fingerprint_type': 1,
            'key': 'fe400b7ac08e79f64fab45cdf866e7672fd3c45c'
        }


class AdderessRecordV4APITests(MozdnsAPITests, ResourceTestCase):
    test_type = AddressRecord

    def setUp(self):
        super(AdderessRecordV4APITests, self).setUp()

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': 'i' + random_label() + "." + self.domain.name,
            'ip_str': "11.{0}.{1}.{2}".format(random_byte(), random_byte(),
                                              random_byte()),
            'ip_type': '4'
        }


class AdderessRecordV6APITests(MozdnsAPITests, ResourceTestCase):
    test_type = AddressRecord

    def setUp(self):
        # Domain.objects.get_or_create(name='arap')
        # Domain.objects.get_or_create(name='ipv6.arap')
        # Domain.objects.get_or_create(name='1.ipv6.arap')
        super(AdderessRecordV6APITests, self).setUp()

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': 'j' + random_label() + "." + self.domain.name,
            'ip_str': "1000:{0}:{1}:{2}::".format(random_byte(), random_byte(),
                                                  random_byte()),
            'ip_type': '6'
        }


class PTRV6APITests(MozdnsAPITests, ResourceTestCase):
    test_type = PTR

    def setUp(self):
        Domain.objects.get_or_create(name='arpa')
        Domain.objects.get_or_create(name='ip6.arpa')
        Domain.objects.get_or_create(name='1.ip6.arpa')
        super(PTRV6APITests, self).setUp()

    def test_fqdn_create(self):
        pass

    def get_domain_and_post_data(self):
        # This is different for classes that have ips instead of fqdns
        domain_name = '1.1.1.1.ip6.arpa'
        root_domain = create_fake_zone(domain_name, suffix="")
        post_data = self.post_data()
        # Get the '_' in SRV records
        post_data['ip_str'] = '1111:123::1f2f'
        return root_domain, post_data

    def post_data(self):
        return {
            'description': 'k' + random_label(),
            'ttl': random_byte(),
            'ip_str': "1000:{0}:{1}:{2}:{3}:{4}::".format(
                random_byte(), random_byte(), random_byte(), random_byte(),
                random_byte()),
            'ip_type': '6',
            'name': random_label()
        }


class PTRV4APITests(MozdnsAPITests, ResourceTestCase):
    test_type = PTR

    def setUp(self):
        Domain.objects.get_or_create(name='arpa')
        Domain.objects.get_or_create(name='in-addr.arpa')
        Domain.objects.get_or_create(name='11.in-addr.arpa')
        super(PTRV4APITests, self).setUp()

    def test_fqdn_create(self):
        pass

    def get_domain_and_post_data(self):
        # This is different for classes that have ips instead of fqdns
        domain_name = '11.22.11.in-addr.arpa'
        root_domain = create_fake_zone(domain_name, suffix="")
        post_data = self.post_data()
        # Get the '_' in SRV records
        post_data['ip_str'] = '11.22.11.1'
        return root_domain, post_data

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'ip_str': gt("11.{0}.{1}.{2}".format(random_byte(), random_byte(),
                         random_byte())),
            'ip_type': '4',
            'name': random_label()
        }


class StaticIntrV4APITests(MozdnsAPITests, ResourceTestCase):
    test_type = StaticInterface

    def setUp(self):
        create_fake_zone('11.in-addr.arpa', suffix="")
        super(StaticIntrV4APITests, self).setUp()
        self.s = System(hostname="foobar")
        self.s.save()

    def compare_data(self, old_data, new_obj_data):
        for key in old_data.keys():
            if key == 'system_hostname':
                self.assertEqual(
                    old_data[key], new_obj_data['system']['hostname'])
                continue
            if key in ('iname', 'system'):
                continue  # StaticInterface needs this done. Too lazy to factor
                          # a comparison function out
            self.assertEqual(old_data[key], new_obj_data[key])

    def test_create_hostname(self):
        post_data = self.post_data()
        del post_data['system']
        post_data['system_hostname'] = self.s.hostname
        resp, post_data = self.generic_create(post_data)
        new_object_url = resp['Location']
        new_resp = self.api_client.get(
            new_object_url, format='json', follow=True
        )
        self.assertValidJSONResponse(new_resp)
        new_obj_data = json.loads(new_resp.content)
        self.compare_data(post_data, new_obj_data)

    def post_data(self):
        return {
            'description': 'm' + random_label(),
            'ttl': random_byte(),
            'mac': '11:22:33:44:55:00',
            'system': '/tasty/v3/system/{0}/'.format(self.s.pk),
            'fqdn': 'a' + random_label() + "." + self.domain.name,
            'iname': 'eth2.4',
            'dhcp_enabled': False,
            'dns_enabled': True,
            'ip_str': "11.255.{0}.{1}".format(random_byte(), random_byte()),
            'ip_type': '4'
        }


class StaticIntrV6APITests(MozdnsAPITests, ResourceTestCase):
    test_type = StaticInterface

    def setUp(self):
        create_fake_zone('2.ip6.arpa', suffix="")
        super(StaticIntrV6APITests, self).setUp()
        self.s = System(hostname="foobar")
        self.s.save()

    def compare_data(self, old_data, new_obj_data):
        for key in old_data.keys():
            if key == 'iname' or key == 'system':
                continue  # StaticInterface needs this done. Too lazy to factor
                          # a comparison function out
            self.assertEqual(old_data[key], new_obj_data[key])

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': 'p' + random_label() + "." + self.domain.name,
            'iname': 'mgmt4',
            'dhcp_enabled': True,
            'dns_enabled': True,
            'mac': '11:22:33:44:55:00',
            'system': '/tasty/v3/system/{0}/'.format(self.s.pk),
            'ip_str': "2000:a{0}:a{1}:a{2}::".format(
                random_byte(), random_byte(), random_byte()),
            'ip_type': '6'
        }
