from django.test import TestCase

from systems.tests.utils import create_fake_host
from systems.models import System
from core.search.compiler.django_compile import compile_to_django
from core.search.compiler.invschema import discover


class SystemTests(TestCase):
    def setUp(self):
        System.objects.all().delete()
        self.hostname = "searching.mozilla.com"
        self.notes = "foo bar baz"
        s = create_fake_host(hostname=self.hostname)
        s.notes = self.notes
        s.save()
        self.status = s.system_status.status

    def cleanUp(self):
        System.objects.all().delete()

    def test_system_field_search_status(self):
        res, error = compile_to_django(
            "sys.system_status__status={0}".format(self.status)
        )
        self.assertFalse(error)
        self.assertEqual(1, res['SYS'].count())
        self.assertEqual(self.hostname, res['SYS'][0].hostname)

    def test_system_field_search_hostname(self):
        res, error = compile_to_django(
            "sys.hostname={0}".format(self.hostname)
        )
        self.assertFalse(error)
        self.assertEqual(1, res['SYS'].count())
        self.assertEqual(self.hostname, res['SYS'][0].hostname)

    def test_system_field_search_notes(self):
        res, error = compile_to_django(
            'sys.notes="{0}"'.format(self.notes)
        )
        self.assertFalse(error)
        self.assertEqual(1, res['SYS'].count())
        self.assertEqual(self.hostname, res['SYS'][0].hostname)

    def test_system_field_search_notes_re(self):
        res, error = compile_to_django(
            'sys.notes=/^foo'.format()
        )
        self.assertFalse(error)
        self.assertEqual(1, res['SYS'].count())
        self.assertEqual(self.hostname, res['SYS'][0].hostname)

    def test_system_field_search_notes_fuzzy(self):
        res, error = compile_to_django(
            'sys.notes~bar'.format()
        )
        self.assertFalse(error)
        self.assertEqual(1, res['SYS'].count())
        self.assertEqual(self.hostname, res['SYS'][0].hostname)

    def test_system_field_search_null_system_rack(self):
        res, error = compile_to_django(
            'sys.system_rack=Null'
        )
        self.assertFalse(error)
        self.assertEqual(1, res['SYS'].count())
        self.assertEqual(self.hostname, res['SYS'][0].hostname)

    def test_system_search_schema(self):
        self.assertTrue('sys.system_rack__site__name' in discover()['SYS'])
