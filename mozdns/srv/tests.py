from django.test import TestCase
from django.core.exceptions import ValidationError

from mozdns.srv.models import SRV
from mozdns.domain.models import Domain


class SRVTests(TestCase):
    def setUp(self):
        self.o = Domain(name="org")
        self.o.save()
        self.o_e = Domain(name="oregonstate.org")
        self.o_e.save()
        self.b_o_e = Domain(name="bar.oregonstate.org")
        self.b_o_e.save()

    def do_generic_add(self, data):
        srv = SRV(**data)
        srv.__repr__()
        srv.save()
        self.assertTrue(srv.details())
        self.assertTrue(srv.get_absolute_url())
        self.assertTrue(srv.get_edit_url())
        self.assertTrue(srv.get_delete_url())
        rsrv = SRV.objects.filter(**data)
        self.assertTrue(len(rsrv) == 1)
        return srv

    def do_remove(self, data):
        srv = self.do_generic_add(data)
        srv.delete()
        rsrv = SRV.objects.filter(**data)
        self.assertTrue(len(rsrv) == 0)

    def test_add_remove_srv(self):
        data = {'label': '_df', 'domain': self.o_e,
                'target': 'relay.oregonstate.edu', 'priority': 2, 'weight':
                2222, 'port': 222}
        self.do_remove(data)
        data = {'label': '_df', 'domain': self.o, 'target':
                'foo.com.nar', 'priority': 1234, 'weight': 23414, 'port': 222}
        self.do_remove(data)
        data = {'label': '_sasfd', 'domain': self.b_o_e,
                'target': 'foo.safasdlcom.nar', 'priority': 12234, 'weight':
                23414, 'port': 222}
        self.do_remove(data)
        data = {'label': '_faf', 'domain': self.o, 'target':
                'foo.com.nar', 'priority': 1234, 'weight': 23414, 'port': 222}
        self.do_remove(data)

        data = {'label': '_bar', 'domain': self.o_e, 'target':
                'relay.oregonstate.edu', 'priority': 2, 'weight': 2222, 'port':
                222}
        self.do_remove(data)

        data = {'label': '_bar', 'domain': self.o_e, 'target':
                '', 'priority': 2, 'weight': 2222, 'port':
                222}
        self.do_remove(data)

    def test_invalid_add_update(self):
        data = {'label': '_df', 'domain': self.o_e,
                'target': 'relay.oregonstate.edu', 'priority': 2, 'weight':
                2222, 'port': 222}
        srv0 = self.do_generic_add(data)
        self.assertRaises(ValidationError, self.do_generic_add, data)
        data = {
            'label': '_df', 'domain': self.o_e,
            'target': 'foo.oregonstate.edu', 'priority': 2, 'weight': 2222,
            'port': 222}

        self.do_generic_add(data)
        self.assertRaises(ValidationError, self.do_generic_add, data)

        srv0.target = "foo.oregonstate.edu"
        self.assertRaises(ValidationError, srv0.save)

        srv0.port = 65536
        self.assertRaises(ValidationError, srv0.save)

        srv0.port = 1
        srv0.priority = 65536
        self.assertRaises(ValidationError, srv0.save)

        srv0.priority = 1
        srv0.weight = 65536
        self.assertRaises(ValidationError, srv0.save)

        srv0.target = "asdfas"
        srv0.label = "no_first"
        self.assertRaises(ValidationError, srv0.save)

        srv0.target = "_df"
        self.assertRaises(ValidationError, srv0.save)
