from django.test import TestCase
from django.test.client import Client
from core.group.models import Group

from mozdns.tests.utils import create_fake_zone
from core.registration.static.models import StaticReg
from systems.tests.utils import create_fake_host


class KVApiTests(TestCase):

    def setUp(self):
        self.c = Client()
        create_fake_zone('10.in-addr.arpa', suffix='')
        root_domain = create_fake_zone('foobar.mozilla.com', suffix='')
        system = create_fake_host(hostname="asdf.mozilla.com")
        sreg = StaticReg.objects.create(
            label='foo', domain=root_domain, system=system,
            ip_type='4', ip_str='10.0.0.0'
        )

        g = Group.objects.create(name="foo")

        self.test_objs = (
            ('groupkeyvalue', g),
            ('staticregkeyvalue', sreg),
            ('keyvalue', system),
        )

    def testCRUD(self):
        for obj_class, o in self.test_objs:
            self.do_stuff(obj_class, o)

    def do_stuff(self, obj_class, o):
        key = 'foo'
        value = 'bar'
        create = '/en-US/core/keyvalue/api/{kv_class}/{obj_pk}/create/'.format(
            kv_class=obj_class, obj_pk=o.pk
        )
        detail = '/en-US/core/keyvalue/api/{kv_class}/{obj_pk}/list/'.format(
            kv_class=obj_class, obj_pk=o.pk
        )

        resp1 = self.c.post(create, {'key': key, 'value': value})
        self.assertEqual(resp1.status_code, 201)

        resp2 = self.c.post(create, {'key': key, 'value': value})
        self.assertEqual(resp2.status_code, 400)

        resp3 = self.c.get(detail)
        self.assertEqual(resp3.status_code, 200)

        resp4 = self.c.get(detail)
        self.assertEqual(resp4.status_code, 200)

        self.assertTrue(1, len(o.keyvalue_set.all()))

        kv = o.keyvalue_set.all()[0]
        update = '/en-US/core/keyvalue/api/{kv_class}/{kv_pk}/update/'.format(
            kv_class=obj_class, kv_pk=kv.pk
        )
        new_value = "happy magic"
        resp5 = self.c.post(update, {'key': key, 'value': new_value})
        self.assertEqual(resp5.status_code, 200)

        kv = o.keyvalue_set.get(pk=kv.pk)
        self.assertEqual(kv.value, new_value)

        # Does bad update do what it's supposed to?
        resp6 = self.c.post(update, {'key': key, 'value': ''})
        self.assertEqual(resp6.status_code, 400)

        kv = o.keyvalue_set.get(pk=kv.pk)
        self.assertEqual(kv.value, new_value)  # Should be no change

        delete = '/en-US/core/keyvalue/api/{kv_class}/{kv_pk}/delete/'.format(
            kv_class=obj_class, kv_pk=kv.pk
        )

        resp6 = self.c.post(delete, {'key': key, 'value': new_value})
        self.assertEqual(resp6.status_code, 204)

        self.assertEqual(0, len(o.keyvalue_set.all()))


class TestCaseUtils(object):
    def localize_url(self, url):
        if 'en-US' not in url:
            url = url.replace('mozdns', 'en-US/mozdns')
        return url
