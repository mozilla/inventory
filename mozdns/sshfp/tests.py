from django.test import TestCase

from mozdns.sshfp.models import SSHFP
from mozdns.domain.models import Domain


class SSHFPTests(TestCase):
    def setUp(self):
        self.o = Domain(name="org")
        self.o.save()
        self.o_e = Domain(name="mozilla.org")
        self.o_e.save()

    def do_generic_add(self, data):
        sshfp = SSHFP(**data)
        sshfp.__repr__()
        sshfp.save()
        self.assertTrue(sshfp.details())
        self.assertTrue(sshfp.get_absolute_url())
        self.assertTrue(sshfp.get_edit_url())
        self.assertTrue(sshfp.get_delete_url())
        rsshfp = SSHFP.objects.filter(**data)
        self.assertEqual(len(rsshfp), 1)
        return sshfp

    def do_remove(self, data):
        sshfp = self.do_generic_add(data)
        sshfp.delete()
        rmx = SSHFP.objects.filter(**data)
        self.assertTrue(len(rmx) == 0)

    def test_add_remove_sshfp(self):
        label = "asdf"
        key = "eee85bca3608ec860fc290bea491ce35d1f0a094"
        s_type = 1
        a_type = 1
        data = {'label': label, 'key': key, 'domain': self.o_e,
                'algorithm_number': a_type, 'fingerprint_type': s_type}
        self.do_generic_add(data)

        label = "asdk"
        key = "eee85bca3608ac860fc290bea491ce35d1f0a094"
        s_type = 1
        a_type = 1
        data = {'label': label, 'key': key, 'domain': self.o_e,
                'algorithm_number': a_type, 'fingerprint_type': s_type}
        self.do_generic_add(data)

        label = "df"
        key = "eee85bca3608ec860fc290bea491ce35d1f0a094"
        s_type = 1
        a_type = 1
        data = {'label': label, 'key': key, 'domain': self.o_e,
                'algorithm_number': a_type, 'fingerprint_type': s_type}
        self.do_generic_add(data)

        label = "12314"
        key = "eee85bca3608ec860fc290bea491ce35d1f0a094"
        s_type = 1
        a_type = 1
        data = {'label': label, 'key': key, 'domain': self.o,
                'algorithm_number': a_type, 'fingerprint_type': s_type}
        self.do_generic_add(data)
