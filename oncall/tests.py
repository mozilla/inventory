from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import Client

from test_utils import setup_test_environment

setup_test_environment()

from oncall.models import OncallAssignment


class OncallTest(TestCase):
    fixtures = ['user_systems_test_data.json']

    def setUp(self):
        self.client = Client()
        u1 = User.objects.get(username='user1@domain.com')
        OncallAssignment.objects.create(oncall_type='desktop', user=u1)
        u2 = User.objects.get(username='user2@domain.com')
        OncallAssignment.objects.create(oncall_type='sysadmin', user=u2)

    def test_initial(self):
        u1 = User.objects.get(username='user1@domain.com')
        self.assertEqual(u1.username, 'user1@domain.com')
        self.assertEqual(u1.get_profile().is_desktop_oncall, True)
        self.assertEqual(u1.get_profile().is_sysadmin_oncall, True)

    def test_desktop_oncall_count(self):
        oncalls = User.objects.select_related().filter(
            userprofile__is_desktop_oncall=1
        )
        self.assertEqual(len(oncalls), 2)

    def test_sysadmin_oncall_count(self):
        oncalls = User.objects.select_related().filter(
            userprofile__is_sysadmin_oncall=1
        )
        self.assertEqual(len(oncalls), 3)

    def test_pgsql_oncall_count(self):
        oncalls = User.objects.select_related().filter(
            userprofile__is_pgsqldba_oncall=1
        )
        self.assertEqual(len(oncalls), 1)

    def test_mysqlsql_oncall_count(self):
        oncalls = User.objects.select_related().filter(
            userprofile__is_mysqldba_oncall=1
        )
        self.assertEqual(len(oncalls), 1)

    def test_oncall_index_page(self):
        """
        Hit the oncall page. Also, hit the old oncall page (eventually remove
        the old page).
        """
        resp = self.client.get('/en-US/oncall/', follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            len(resp.context['form'].fields['desktop'].choices), 2
        )
        self.assertEqual(
            len(resp.context['form'].fields['sysadmin'].choices), 3
        )

        resp = self.client.get('/en-US/systems/oncall/', follow=True)
        self.assertEqual(resp.status_code, 200)

    def test_getoncall(self):
        """
        This test tests for valid http responses and does not do tests on the
        return data.
        """
        resp = self.client.get(
            '/en-US/oncall/getoncall/sysadmin/', follow=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.content)

        resp = self.client.get('/en-US/oncall/getoncall/desktop/', follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.content)
