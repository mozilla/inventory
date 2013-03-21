# These tests are similar to the ones in the scripts directory. They not ran on
# real data so the testing db needs to be filled with info.
import os
from django.test.client import Client
from django.test import TestCase

from mozdns.soa.models import SOA
from mozdns.domain.models import Domain
from mozdns.address_record.models import AddressRecord
from mozdns.view.models import View
from mozdns.tests.utils import random_label, random_byte
from mozdns.mozbind.builder import DNSBuilder, BuildError
from mozdns.tests.utils import create_fake_zone

from core.task.models import Task


from scripts.dnsbuilds.tests.build_tests import BuildScriptTests


class MockBuildScriptTests(BuildScriptTests, TestCase):
    def setUp(self):
        Domain.objects.get_or_create(name="arpa")
        Domain.objects.get_or_create(name="in-addr.arpa")
        self.r1, _ = Domain.objects.get_or_create(name="10.in-addr.arpa")
        Domain.objects.get_or_create(name="com")
        Domain.objects.get_or_create(name="mozilla.com")
        self.cleint = Client()
        super(MockBuildScriptTests, self).setUp()
        self.stop_update_file = '/tmp/fake/stop.update'

    def get_post_data(self, random_str):
        """Return a valid set of data"""
        return {
            'root_domain': '{0}.{0}.mozilla.com'.format(
            random_label() + random_str),
            'soa_primary': 'ns1.mozilla.com',
            'soa_contact': 'noc.mozilla.com',
            'nameserver_1': 'ns1.mozilla.com',
            'nameserver_2': 'ns2.mozilla.com',
            'nameserver_3': 'ns3.mozilla.com',
            'ttl_1': random_byte(),
            'ttl_2': random_byte(),
            'ttl_3': random_byte(),
        }

    def test_build_zone(self):
        create_fake_zone('asdf1')
        b = DNSBuilder(STAGE_DIR=self.stage_dir, PROD_DIR=self.prod_dir,
                       LOCK_FILE=self.lock_file, LOG_SYSLOG=False,
                       FIRST_RUN=True, PUSH_TO_PROD=False,
                       STOP_UPDATE_FILE=self.stop_update_file)
        b.build_dns()
        create_fake_zone('asdf2')
        b.build_dns()
        create_fake_zone('asdf3')
        create_fake_zone('asdf4')
        b.build_dns()
        create_fake_zone('asdf5')
        b.build_dns()

    def test_change_a_record(self):
        root_domain = create_fake_zone('asdfz1')
        b = DNSBuilder(STAGE_DIR=self.stage_dir, PROD_DIR=self.prod_dir,
                       LOCK_FILE=self.lock_file, LOG_SYSLOG=False,
                       FIRST_RUN=True, PUSH_TO_PROD=False,
                       STOP_UPDATE_FILE=self.stop_update_file)

        b.build_dns()  # This won't check anything in since PUSH_TO_PROD==False
        self.assertEqual((26, 0), b.svn_lines_changed(b.PROD_DIR))
        b.PUSH_TO_PROD = True
        b.build_dns()  # This checked stuff in

        # no lines should have changed
        b.build_dns()
        self.assertEqual((0, 0), b.svn_lines_changed(b.PROD_DIR))

        # Now add a record.
        a, c = AddressRecord.objects.get_or_create(
            label='', domain=root_domain, ip_str="10.0.0.1", ip_type='4'
        )
        a.views.add(View.objects.get_or_create(name='private')[0])
        if not c:
            a.ttl = 8
            a.save()

        self.assertTrue(SOA.objects.get(pk=root_domain.soa.pk).dirty)
        tmp_serial = SOA.objects.get(pk=root_domain.soa.pk).serial

        b.PUSH_TO_PROD = False  # Task isn't deleted
        b.build_dns()  # Serial get's incrimented
        self.assertEqual(
            SOA.objects.get(pk=root_domain.soa.pk).serial, tmp_serial + 1
        )
        self.assertFalse(SOA.objects.get(pk=root_domain.soa.pk).dirty)
        # added new record (1) and new serials (2 for both views), old serials
        # removed.
        self.assertEqual((3, 2), b.svn_lines_changed(b.PROD_DIR))

        tmp_serial = SOA.objects.get(pk=root_domain.soa.pk).serial
        self.assertFalse(SOA.objects.get(pk=root_domain.soa.pk).dirty)

        b.PUSH_TO_PROD = True
        b.build_dns()
        self.assertFalse(SOA.objects.get(pk=root_domain.soa.pk).dirty)
        # Serial is again incremented because PUSH_TO_PROD was False during the
        # last build. When PUSH_TO_PROD is false, no scheduled tasts are
        # deleted so we should still see this soa being rebuilt.
        self.assertEqual(
            SOA.objects.get(pk=root_domain.soa.pk).serial, tmp_serial + 1
        )
        self.assertEqual((0, 0), b.svn_lines_changed(b.PROD_DIR))

        # no lines should have changed if we would have built again

        self.assertFalse(SOA.objects.get(pk=root_domain.soa.pk).dirty)
        tmp_serial = SOA.objects.get(pk=root_domain.soa.pk).serial
        b.PUSH_TO_PROD = False
        b.build_dns()
        self.assertEqual(SOA.objects.get(pk=root_domain.soa.pk).serial,
                         tmp_serial)
        self.assertFalse(SOA.objects.get(pk=root_domain.soa.pk).dirty)
        self.assertEqual((0, 0), b.svn_lines_changed(b.PROD_DIR))

    def test_one_file_svn_lines_changed(self):
        b = DNSBuilder(STAGE_DIR=self.stage_dir, PROD_DIR=self.prod_dir,
                       LOCK_FILE=self.lock_file, LOG_SYSLOG=False,
                       FIRST_RUN=True, PUSH_TO_PROD=False,
                       STOP_UPDATE_FILE=self.stop_update_file)
        test_file = os.path.join(self.prod_dir, 'test')
        with open(test_file, 'w+') as fd:
            fd.write('line 1\n')
        lc = b.svn_lines_changed(b.PROD_DIR)
        self.assertEqual((1, 0), lc)
        b.svn_checkin(lc)

        with open(test_file, 'w+') as fd:
            fd.write('line 1\nline 2\n')

        lc = b.svn_lines_changed(b.PROD_DIR)
        self.assertEqual((1, 0), lc)
        b.svn_checkin(lc)

        with open(test_file, 'w+') as fd:
            fd.write('line 1\n')

        lc = b.svn_lines_changed(b.PROD_DIR)
        self.assertEqual((0, 1), lc)
        b.svn_checkin(lc)

    def test_too_many_config_lines_changed(self):
        create_fake_zone('asdf86')
        root_domain1 = create_fake_zone('asdf87')
        root_domain2 = create_fake_zone('asdf88')
        root_domain3 = create_fake_zone('asdf89')
        b = DNSBuilder(STAGE_DIR=self.stage_dir, PROD_DIR=self.prod_dir,
                       LOCK_FILE=self.lock_file, LOG_SYSLOG=False,
                       FIRST_RUN=True, PUSH_TO_PROD=True,
                       STOP_UPDATE_FILE=self.stop_update_file)
        b.build_dns()
        for ns in root_domain1.nameserver_set.all():
            ns.delete()

        b.build_dns()  # One zone removed should be okay

        for ns in root_domain2.nameserver_set.all():
            ns.delete()

        for ns in root_domain3.nameserver_set.all():
            ns.delete()

        self.assertRaises(BuildError, b.build_dns)

    def test_two_file_svn_lines_changed(self):
        b = DNSBuilder(STAGE_DIR=self.stage_dir, PROD_DIR=self.prod_dir,
                       LOCK_FILE=self.lock_file, LOG_SYSLOG=False,
                       FIRST_RUN=True, PUSH_TO_PROD=False,
                       STOP_UPDATE_FILE=self.stop_update_file)
        test1_file = os.path.join(self.prod_dir, 'test1')
        test2_file = os.path.join(self.prod_dir, 'test2')
        with open(test1_file, 'w+') as fd:
            fd.write('line 1.1\n')

        lc = b.svn_lines_changed(b.PROD_DIR)
        self.assertEqual((1, 0), lc)
        b.svn_checkin(lc)

        with open(test1_file, 'w+') as fd:
            fd.write('line 1.1\nline 1.2\n')
        with open(test2_file, 'w+') as fd:
            fd.write('line 2.1\nline 2.2\n')

        lc = b.svn_lines_changed(b.PROD_DIR)
        self.assertEqual((3, 0), lc)
        b.svn_checkin(lc)

        with open(test1_file, 'w+') as fd:
            fd.write('line 1\n')

        lc = b.svn_lines_changed(b.PROD_DIR)
        self.assertEqual((1, 2), lc)
        b.svn_checkin(lc)

        with open(test1_file, 'w+') as fd:
            fd.write('line 1.1\nline 1.2\n')
        with open(test2_file, 'w+') as fd:
            fd.write('line 2.3\nline 2.4\n')

        lc = b.svn_lines_changed(b.PROD_DIR)
        self.assertEqual((4, 3), lc)
        b.svn_checkin(lc)

    def test_svn_conflict(self):
        """
        This uses tasks as a block box measurement to see if conflicts are
        being handled
        """
        root_domain = create_fake_zone('conflict')
        b1 = DNSBuilder(STAGE_DIR=self.stage_dir, PROD_DIR=self.prod_dir,
                        LOCK_FILE=self.lock_file, LOG_SYSLOG=False,
                        FIRST_RUN=True, PUSH_TO_PROD=True,
                        STOP_UPDATE_FILE=self.stop_update_file)

        b1.build_dns()  # This checked stuff in

        # Check the repo out somewhere elst
        command_str = "svn co file://{0} {1}".format(
            self.svn_repo, self.prod_dir2
        )
        b1.shell_out(command_str)

        # Calculate the path to the zone file so we can tamper with it.
        fm = b1.get_file_meta(
            View.objects.get(name='public'), root_domain,
            root_domain.soa
        )

        # Make local changes
        fname = fm['prod_fname'].replace(self.prod_dir, self.prod_dir2)
        with open(fname, 'a') as fd:
            fd.write(";foobar")

        # Check those changes in.
        b1.PROD_DIR = self.prod_dir2  # Cheat and swap the dirs
        b1.vcs_checkin()

        b1.PROD_DIR = self.prod_dir  # Fix our little cheat
        b1.FORCE = True  # Force a build

        # Add something to the end of the file to cause a collision
        a = AddressRecord.objects.create(
            label="zeenada", domain=root_domain, ip_type='4',
            ip_str='255.0.0.0'
        )
        a.views.add(View.objects.get(name='public'))

        # Alright, we should have conflicts here. See if we detect it by
        # counting how many tasks need to be serviced. If the number remains
        # the same that means we aborted the build due to a conflict
        pre_task_count = Task.objects.all().count()
        b1.build_dns()
        post_task_count = Task.objects.all().count()
        self.assertEqual(pre_task_count, post_task_count)

        # Conflicts should be resolved. Let's see if we build successfully
        pre_task_count = Task.objects.all().count()
        b1.build_dns()
        post_task_count = Task.objects.all().count()
        self.assertTrue(pre_task_count != 0)
        self.assertEqual(0, post_task_count)
