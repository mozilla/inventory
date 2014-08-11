from django.test import TestCase, TransactionTestCase
from django.test.client import Client

from systems.models import System
from systems.tests.utils import create_fake_host

from core.service.models import Service, Dependency
from core.site.models import Site

import simplejson as json


class BaseServiceTests(object):
    def setUp(self):
        self.client = Client()
        self.site = Site.objects.create(full_name='foo')
        self.s1 = Service.objects.create(name='ldap', site=self.site)
        self.sys1 = create_fake_host(hostname='foobar1.mozilla.com')
        self.sys2 = create_fake_host(hostname='foobar2.mozilla.com')
        self.sys3 = create_fake_host(hostname='foobar3.mozilla.com')

        self.s1.systems.add(self.sys1)
        self.s1.systems.add(self.sys2)
        self.s1.systems.add(self.sys3)
        self.s1.save()

        self.s2 = Service.objects.create(name='dns and stuff')
        sys4 = create_fake_host(hostname='foobar4.mozilla.com')
        sys5 = create_fake_host(hostname='foobar5.mozilla.com')
        sys6 = create_fake_host(hostname='foobar6.mozilla.com')

        self.s2.systems.add(sys4)
        self.s2.systems.add(sys5)
        self.s2.systems.add(sys6)
        self.s2.save()

        self.s3 = Service.objects.create(name='dns and stuff', site=self.site)

        # make s1 depend on s2 and s3
        Dependency.objects.get_or_create(
            dependant=self.s1, provider=self.s2
        )
        Dependency.objects.get_or_create(
            dependant=self.s1, provider=self.s3
        )

    def export_services(self, query):
        resp = self.client.get(
            '/core/service/export/', {'search': query}, follow=True
        )
        return json.loads(resp.content), resp

    def import_services(self, data):
        resp = self.client.post(
            '/en-US/core/service/import/', data=json.dumps(data),
            content_type='application/json'
        )
        return json.loads(resp.content), resp

    def get_service(self, iql_stmt):
        sblob, resp = self.export_services(iql_stmt)
        self.assertEqual(200, resp.status_code, resp.content)
        self.assertEqual(
            1, len(sblob['services']), "Should have seen only one service"
        )
        return sblob


class ServiceAPITests(BaseServiceTests, TestCase):
    def test_export(self):
        actual1 = self.get_service(self.s1.iql_stmt())
        self.assertEqual(
            actual1['services'][0]['systems'],
            ['foobar1.mozilla.com', 'foobar2.mozilla.com',
             'foobar3.mozilla.com']
        )

        actual2 = self.get_service(self.s2.iql_stmt())
        self.assertEqual(
            actual2['services'][0]['systems'],
            ['foobar4.mozilla.com', 'foobar5.mozilla.com',
             'foobar6.mozilla.com']
        )

    def test_import_new_service(self):
        # Make sure importing a new service works
        services_blob = json.loads("""
        {{
            "http_status": 200,
            "services": [
                {{
                    "alias": "",
                    "business_owner": "",
                    "category": "",
                    "description": "",
                    "impact": "",
                    "name": "a.dns",
                    "notes": "",
                    "parent_service": "{0}",
                    "site": "{1}",
                    "systems": [
                        "{2}"
                    ],
                    "tech_owner": "",
                    "usage_frequency": "",
                    "used_by": ""
                }},
                {{
                    "alias": "",
                    "business_owner": "",
                    "category": "",
                    "description": "",
                    "impact": "",
                    "name": "b.dns",
                    "notes": "",
                    "parent_service": "",
                    "site": "{1}",
                    "systems": [
                        "{2}"
                    ],
                    "tech_owner": "",
                    "usage_frequency": "",
                    "used_by": ""
                }}
            ]
        }}
        """.strip().format(self.s1.iql_stmt(), self.site.full_name, self.sys1))
        _, resp = self.import_services(services_blob)
        self.assertEqual(resp.status_code, 200, resp.content)
        a = Service.objects.get(name='a.dns')
        b = Service.objects.get(name='b.dns')
        self.assertEqual(a.parent_service, self.s1)
        self.assertFalse(b.parent_service)

    def test_import_create_delete_create(self):
        # export, delete, import, ensure things are the same
        original = self.get_service(self.s1.iql_stmt())

        # delete and then recreate. we are testing the ability to associate
        # systems to a service, so nuking it will kill all the relationships
        # we are trying to test the creation of.
        systems_count = System.objects.count()
        self.s1.delete()

        # Make sure cascade delete isnt a thing
        self.assertEqual(
            systems_count, System.objects.count(),
            "woah! systems were deleted when they should not have been"
        )
        self.s1 = Service.objects.create(name='ldap', site=self.site)

        # set some extra stuff to make sure it is saved properly
        original['services'][0]['tech_owner'] = 'wesley'
        original['services'][0]['pk'] = self.s1.pk
        _, resp = self.import_services(original)
        self.assertEqual(resp.status_code, 200, resp.content)

        new = self.get_service(self.s1.iql_stmt())
        self.assertEqual(original, new)

    def test_add_parent_service(self):
        # export, add super service, import, verify, remove super service,
        # import, verify

        # export
        original = self.get_service(self.s1.iql_stmt())

        self.assertEqual(
            original['services'][0]['parent_service'],
            'None'
        )

        # add super service
        original['services'][0]['parent_service'] = self.s2.iql_stmt()

        # import
        _, resp = self.import_services(original)
        self.assertEqual(resp.status_code, 200, resp.content)

        # export and verify
        self.assertEqual(
            Service.objects.get(pk=self.s1.pk).parent_service,
            self.s2
        )
        new = self.get_service(self.s1.iql_stmt())
        self.assertEqual(
            new['services'][0]['parent_service'],
            self.s2.iql_stmt()
        )

        # remove super service
        new['services'][0]['parent_service'] = 'NONE'

        # import
        _, resp = self.import_services(new)
        self.assertEqual(resp.status_code, 200, resp.content)

        # export and verify
        self.assertEqual(
            Service.objects.get(pk=self.s1.pk).parent_service,
            None
        )
        new_again = self.get_service(self.s1.iql_stmt())
        self.assertEqual(
            new_again['services'][0]['parent_service'],
            'None'
        )

    def test_import_add_system(self):
        # export, add one system, assert the sytem was added
        original = self.get_service(self.s1.iql_stmt())

        s = create_fake_host(hostname='hihihi.mozilla.com')

        original['services'][0]['systems'].append(s.hostname)

        self.assertFalse(self.s1.systems.filter(hostname=s.hostname).exists())

        _, resp = self.import_services(original)
        self.assertEqual(resp.status_code, 200, resp.content)

        self.assertTrue(self.s1.systems.filter(hostname=s.hostname).exists())

    def test_import_remove_system(self):
        # export, add one system, assert the sytem was added, remove it, assert
        # it was removed
        sblob = self.get_service(self.s1.iql_stmt())

        # create
        s = create_fake_host(hostname='hihihi.mozilla.com')

        # add
        sblob['services'][0]['systems'].append(s.hostname)

        # new host shouldn't exist in the service
        self.assertFalse(self.s1.systems.filter(hostname=s.hostname).exists())

        # import
        _, resp = self.import_services(sblob)
        self.assertEqual(resp.status_code, 200, resp.content)

        # new host should now exist in the service
        self.assertTrue(self.s1.systems.filter(hostname=s.hostname).exists())

        # refresh the blob for good measure
        sblob = self.get_service(self.s1.iql_stmt())

        # make sure the system's hostname is in the blob (this may be
        # redundant)
        self.assertTrue(s.hostname in sblob['services'][0]['systems'])
        # remove the host form the export blob
        sblob['services'][0]['systems'].remove(s.hostname)

        # import the blob
        _, resp = self.import_services(sblob)
        self.assertEqual(resp.status_code, 200, resp.content)

        # make sure it was removed
        self.assertFalse(self.s1.systems.filter(hostname=s.hostname).exists())

    def test_add_deps(self):
        s4 = Service.objects.create(name='foo', site=self.site)
        sblob = self.get_service(s4.iql_stmt())
        sblob['services'][0]['depends_on'] = [
            self.s1.iql_stmt(),
            self.s2.iql_stmt(),
            self.s3.iql_stmt()
        ]

        # import the blob
        _, resp = self.import_services(sblob)
        self.assertEqual(resp.status_code, 200, resp.content)

        pk_list = map(lambda d: d.provider.pk, s4.providers.all())
        self.assertTrue(self.s1.pk in pk_list)
        self.assertTrue(self.s2.pk in pk_list)
        self.assertTrue(self.s3.pk in pk_list)

    def test_import_remove_add_dependant_service(self):
        # This test does: export all state, remove a dep from s1, import,
        # ensure the remove worked, add a dep to s1, import, make sure the
        # add worked

        # get an export so we can play with it
        sblob = self.get_service(self.s1.iql_stmt())

        # remember how many deps we started with
        old_dep_count = Dependency.objects.count()

        self.assertEqual(
            2, len(sblob['services'][0]['depends_on'])
        )
        # remove a dep
        sblob['services'][0]['depends_on'].remove(self.s2.iql_stmt())
        # Make sure the s3 service is still there
        self.assertTrue(
            self.s3.iql_stmt() in sblob['services'][0]['depends_on']
        )

        # import the new state
        _, resp = self.import_services(sblob)
        self.assertEqual(resp.status_code, 200, resp.content)

        # refresh state
        sblob = self.get_service(self.s1.iql_stmt())

        # we should only see one dep now
        self.assertEqual(
            1, len(sblob['services'][0]['depends_on'])
        )

        # make sure we deleted the right one. the old dep should still be there
        self.assertTrue(
            self.s3.iql_stmt() in sblob['services'][0]['depends_on']
        )

        # Make sure we only deleted one dep
        new_dep_count = Dependency.objects.count()
        self.assertEqual(
            old_dep_count - 1, new_dep_count,
            "It doesn't look like a dependency was deleted"
        )

        # add back the dep
        sblob['services'][0]['depends_on'].append(self.s2.iql_stmt())

        # import the new state
        _, resp = self.import_services(sblob)
        self.assertEqual(resp.status_code, 200, resp.content)

        # refresh state
        sblob = self.get_service(self.s1.iql_stmt())

        # ensure the new dep is there
        self.assertTrue(
            self.s2.iql_stmt() in sblob['services'][0]['depends_on']
        )

    def test_bad_impact_option(self):
        sblob, resp = self.export_services(
            'service.name="{0}"'.format(self.s1.name)
        )
        self.assertEqual(200, resp.status_code, resp.content)
        self.assertEqual(
            1, len(sblob['services']), "Should have seen only one service"
        )

        sblob['services'][0]['impact'] = 'not-that-high'

        resp_json, resp = self.import_services(sblob)
        self.assertEqual(
            resp.status_code, 400, "Expected error but got: "
            "{0}".format(resp.content)
        )

        self.assertTrue(
            'errors' in resp_json, "expected to see an 'errors' key"
        )

    def test_create_duplicate_service(self):
        sblob, resp = self.export_services(
            'service.name="{0}"'.format(self.s1.name)
        )
        self.assertEqual(200, resp.status_code, resp.content)
        self.assertEqual(
            1, len(sblob['services']), "Should have seen only one service"
        )

        del sblob['services'][0]['pk']

        resp_json, resp = self.import_services(sblob)
        self.assertEqual(200, resp.status_code, resp.content)

    def test_implicit_update(self):
        # Make sure updating works when the pk isn't present causing the
        # service to be looked up by name/site pair
        sblob, resp = self.export_services(
            'service.name="{0}"'.format(self.s1.name)
        )
        self.assertEqual(200, resp.status_code, resp.content)
        self.assertEqual(
            1, len(sblob['services']), "Should have seen only one service"
        )

        del sblob['services'][0]['pk']
        sblob['services'][0]['notes'] = 'foobar'

        resp_json, resp = self.import_services(sblob)
        self.assertEqual(200, resp.status_code, resp.content)
        self.assertEqual('foobar', Service.objects.get(pk=self.s1.pk).notes)

    def test_explicit_update(self):
        # Make sure updating works using the pk
        sblob, resp = self.export_services(
            'service.name="{0}"'.format(self.s1.name)
        )
        self.assertEqual(200, resp.status_code, resp.content)
        self.assertEqual(
            1, len(sblob['services']), "Should have seen only one service"
        )

        sblob['services'][0]['name'] = 'foobar'

        resp_json, resp = self.import_services(sblob)
        self.assertEqual(200, resp.status_code, resp.content)
        self.assertEqual('foobar', Service.objects.get(pk=self.s1.pk).name)

    def test_non_existant_parent_service(self):
        sblob, resp = self.export_services(
            'service.name="{0}"'.format(self.s1.name)
        )
        self.assertEqual(200, resp.status_code, resp.content)
        self.assertEqual(
            1, len(sblob['services']), "Should have seen only one service"
        )

        sblob['services'][0]['parent_service'] = 'crap as a service'

        resp_json, resp = self.import_services(sblob)
        self.assertEqual(
            resp.status_code, 400, "Expected error but got: "
            "{0}".format(resp.content)
        )

        self.assertTrue(
            'errors' in resp_json, "expected to see an 'errors' key"
        )

    def test_non_existant_site(self):
        sblob, resp = self.export_services(
            'service.name="{0}"'.format(self.s1.name)
        )
        self.assertEqual(200, resp.status_code, resp.content)
        self.assertEqual(
            1, len(sblob['services']), "Should have seen only one service"
        )

        sblob['services'][0]['site'] = 'asdf'

        resp_json, resp = self.import_services(sblob)
        self.assertEqual(
            resp.status_code, 400, "Expected error but got: "
            "{0}".format(resp.content)
        )

        self.assertTrue(
            'errors' in resp_json, "expected to see an 'errors' key"
        )


class ServiceMangleAPITests(BaseServiceTests, TransactionTestCase):
    # These tests rely on db transaction logic and run really slow because they
    # use TransactionTestCase, so they get their own class.

    def tearDown(self):
        # Be hygenic
        Site.objects.all().delete()
        System.objects.all().delete()
        Service.objects.all().delete()

    def test_non_existant_system(self):
        # add two systems: one real one and one with a hostname that doesn't
        # exist. Make sure the real one didn't get associated with the service
        # (this checks wheter we rolledback or not.)

        # a real new system
        system = create_fake_host(hostname='foobar9.mozilla.com')
        sblob, resp = self.export_services(
            'service.name="{0}"'.format(self.s1.name)
        )
        self.assertEqual(200, resp.status_code, resp.content)
        self.assertEqual(
            1, len(sblob['services']), "Should have seen only one service"
        )

        sblob['services'][0]['systems'] += [system.hostname, 'not.real.com']

        resp_json, resp = self.import_services(sblob)
        self.assertEqual(
            resp.status_code, 400, "Expected error but got: "
            "{0}".format(resp.content)
        )

        self.assertTrue(
            'errors' in resp_json, "expected to see an 'errors' key"
        )

        # The real system still sholdn't be in the service
        system = system.refresh()
        self.assertFalse(system.service_set.exists())
