from django.test import TestCase
from django.core.exceptions import ValidationError

from core.site.models import Site


class SiteTests(TestCase):

    def test_create(self):
        site = Site.objects.create(full_name='foo')
        self.assertTrue(site.pk)
        self.assertFalse(site.parent)

        site.full_name = 'foo.bar'
        site.save()
        self.assertEqual(site.name, 'foo')
        parent = Site.objects.get(full_name='bar')
        self.assertEqual(site.parent, parent)

    def test_bad_names(self):
        obj_count = Site.objects.count()

        self.assertRaises(ValidationError, Site(full_name='foo.').save)
        self.assertEqual(obj_count, Site.objects.count())

        self.assertRaises(ValidationError, Site(full_name='.').save)
        self.assertEqual(obj_count, Site.objects.count())

        self.assertRaises(ValidationError, Site(full_name='foo.bar.').save)
        self.assertEqual(obj_count, Site.objects.count())

        self.assertRaises(ValidationError, Site(full_name='foo.bar.').save)
        self.assertEqual(obj_count, Site.objects.count())

        self.assertRaises(ValidationError, Site(full_name='woo..foo.baz').save)
        self.assertEqual(obj_count, Site.objects.count())

    def test_dup(self):
        Site(full_name='foo.bar.baz.bri').save()
        obj_count = Site.objects.count()

        self.assertRaises(
            ValidationError, Site(full_name='foo.bar.baz.bri').save)
        self.assertEqual(obj_count, Site.objects.count())
