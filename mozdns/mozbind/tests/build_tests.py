import os
import subprocess
import shutil
import shlex

from django.test.client import Client
from django.test import TestCase

from mozdns.soa.models import SOA
from mozdns.domain.models import Domain
from mozdns.address_record.models import AddressRecord
from mozdns.view.models import View
from mozdns.tests.utils import random_label, random_byte
from mozdns.mozbind.builder import DNSBuilder, BuildError
from mozdns.delete_zone.utils import delete_zone_helper
from mozdns.tests.utils import create_fake_zone

from core.task.models import Task


from settings.dnsbuilds import TEST_PREFIX
TEST_PREFIX = TEST_PREFIX.rstrip('/')


class MockBuildScriptTests(TestCase):
    def setUp(self):
        Task.objects.all().delete()
        for soa in SOA.objects.all():
            delete_zone_helper(soa.root_domain.name)
        Domain.objects.get_or_create(name="arpa")
        Domain.objects.get_or_create(name="in-addr.arpa")
        self.r1, _ = Domain.objects.get_or_create(name="10.in-addr.arpa")
        Domain.objects.get_or_create(name="com")
        Domain.objects.get_or_create(name="mozilla.com")
        self.cleint = Client()

        # Build file system assets
        self.stage_dir = '{0}/stage/inv_zones/'.format(TEST_PREFIX)
        self.svn_dir = '{0}/dnsconfig/'.format(TEST_PREFIX)
        self.prod_dir = '{0}/dnsconfig/inv_zones/'.format(TEST_PREFIX)
        self.prod_dir2 = '{0}/dnsconfig/inv_zones2/'.format(TEST_PREFIX)
        self.svn_repo = '{0}/svn_repo'.format(TEST_PREFIX)
        self.lock_file = '{0}/lock.fake'.format(TEST_PREFIX)
        self.stop_update = '{0}/stop.update'.format(TEST_PREFIX)
        self.re_test_file = '{0}/re_test'.format(TEST_PREFIX)

        #os.chdir(os.path.join(TEST_PREFIX, ".."))
        if os.path.isdir(TEST_PREFIX):
            shutil.rmtree(TEST_PREFIX)
        os.makedirs(TEST_PREFIX)
        #os.makedirs(self.svn_repo)

        command_str = "svnadmin create {0}".format(self.svn_repo)
        rets = subprocess.Popen(shlex.split(command_str),
                                stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE)
        stdout, stderr = rets.communicate()
        self.assertEqual(0, rets.returncode, stderr)

        command_str = "svn co file://{0} {1}".format(self.svn_repo,
                                                     self.prod_dir)
        rets = subprocess.Popen(shlex.split(command_str),
                                stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE)
        stdout, stderr = rets.communicate()
        self.assertEqual(0, rets.returncode, stderr)

        command_str = "svn co file://{0} {1}".format(self.svn_repo,
                                                     self.prod_dir2)
        rets = subprocess.Popen(shlex.split(command_str),
                                stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE)
        stdout, stderr = rets.communicate()
        self.assertEqual(0, rets.returncode, stderr)

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
                       STOP_UPDATE_FILE=self.stop_update)
        b.build_dns()
        create_fake_zone('asdf2')
        b.build_dns()
        create_fake_zone('asdf3')
        create_fake_zone('asdf4')
        b.build_dns()
        create_fake_zone('asdf5')
        b.build_dns()

    def test_change_a_record(self):
        b = DNSBuilder(STAGE_DIR=self.stage_dir, PROD_DIR=self.prod_dir,
                       LOCK_FILE=self.lock_file, LOG_SYSLOG=False,
                       FIRST_RUN=True, PUSH_TO_PROD=False,
                       STOP_UPDATE_FILE=self.stop_update)

        b.svn_lines_changed(b.PROD_DIR)
        b.PUSH_TO_PROD = False

        root_domain = create_fake_zone('asdfz1')

        b.build_dns()  # This won't check anything in since PUSH_TO_PROD==False
        self.assertEqual((28, 0), b.svn_lines_changed(b.PROD_DIR))
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

        # We just updated a zone so a full build shouldn't be triggered
        self.assertFalse(Task.dns_full.all())

        # we should see one zone being rebuilt
        self.assertEqual(1, Task.dns_incremental.all().count())

        self.assertTrue(SOA.objects.get(pk=root_domain.soa.pk).dirty)
        tmp_serial = SOA.objects.get(pk=root_domain.soa.pk).serial

        b.PUSH_TO_PROD = False  # Task isn't deleted
        b.build_dns()  # Serial get's incrimented

        # Since push-to-prod is false, we should still see the tasks in the
        # same state
        self.assertFalse(Task.dns_full.all())
        self.assertEqual(1, Task.dns_incremental.all().count())

        self.assertEqual(
            SOA.objects.get(pk=root_domain.soa.pk).serial, tmp_serial + 1
        )

        # The dirty bit should still be true because we didn't check things in
        self.assertTrue(SOA.objects.get(pk=root_domain.soa.pk).dirty)

        # added new record (1) and new serials (2 for both views), old serials
        # removed.
        self.assertEqual((3, 2), b.svn_lines_changed(b.PROD_DIR))

        tmp_serial = SOA.objects.get(pk=root_domain.soa.pk).serial

        b.PUSH_TO_PROD = True
        b.build_dns()

        # Since push-to-prod is true all tasks should be back 0
        self.assertFalse(Task.dns_full.all())
        self.assertFalse(Task.dns_incremental.all())

        self.assertFalse(SOA.objects.get(pk=root_domain.soa.pk).dirty)

        # Serial is again incremented because PUSH_TO_PROD was False during the
        # last build.
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

        # Nothing changed
        self.assertFalse(Task.dns_full.all())
        self.assertFalse(Task.dns_incremental.all())

        self.assertEqual(SOA.objects.get(pk=root_domain.soa.pk).serial,
                         tmp_serial)
        self.assertFalse(SOA.objects.get(pk=root_domain.soa.pk).dirty)
        self.assertEqual((0, 0), b.svn_lines_changed(b.PROD_DIR))

    def test_one_file_svn_lines_changed(self):
        b = DNSBuilder(STAGE_DIR=self.stage_dir, PROD_DIR=self.prod_dir,
                       LOCK_FILE=self.lock_file, LOG_SYSLOG=False,
                       FIRST_RUN=True, PUSH_TO_PROD=False,
                       STOP_UPDATE_FILE=self.stop_update)
        test_file = os.path.join(self.prod_dir, 'test')
        with open(test_file, 'w+') as fd:
            fd.write('line 1\n')
        lc = b.svn_lines_changed(self.prod_dir)
        self.assertEqual((1, 0), lc)
        b.svn_checkin(lc)

        with open(test_file, 'w+') as fd:
            fd.write('line 1\nline 2\n')

        lc = b.svn_lines_changed(self.prod_dir)
        self.assertEqual((1, 0), lc)
        b.svn_checkin(lc)

        with open(test_file, 'w+') as fd:
            fd.write('line 1\n')

        lc = b.svn_lines_changed(self.prod_dir)
        self.assertEqual((0, 1), lc)
        b.svn_checkin(lc)

    def test_too_many_config_lines_changed(self):
        create_fake_zone('asdf86')
        root_domain1 = create_fake_zone('asdf87')
        root_domain2 = create_fake_zone('asdf88')
        root_domain3 = create_fake_zone('asdf89')
        create_fake_zone('asdf90')
        b = DNSBuilder(STAGE_DIR=self.stage_dir, PROD_DIR=self.prod_dir,
                       LOCK_FILE=self.lock_file, LOG_SYSLOG=False,
                       FIRST_RUN=True, PUSH_TO_PROD=True,
                       STOP_UPDATE_FILE=self.stop_update)
        self.assertTrue(Task.dns_full.all())
        self.assertFalse(Task.dns_incremental.all().count())
        b.build_dns()

        self.assertFalse(Task.dns_full.all())
        self.assertFalse(Task.dns_incremental.all())

        # deleting one ns
        for ns in root_domain1.nameserver_set.all():
            ns.delete()

        self.assertTrue(Task.dns_full.all())
        self.assertEqual(1, Task.dns_incremental.all().count())

        b.build_dns()  # One zone removed should be okay

        for ns in root_domain2.nameserver_set.all():
            ns.delete()

        for ns in root_domain3.nameserver_set.all():
            ns.delete()

        b.PUSH_TO_PROD = True
        self.assertRaises(BuildError, b.build_dns)

    def test_two_file_svn_lines_changed(self):
        b = DNSBuilder(STAGE_DIR=self.stage_dir, PROD_DIR=self.prod_dir,
                       LOCK_FILE=self.lock_file, LOG_SYSLOG=False,
                       FIRST_RUN=True, PUSH_TO_PROD=False,
                       STOP_UPDATE_FILE=self.stop_update)
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
                        STOP_UPDATE_FILE=self.stop_update)

        b1.build_dns()  # This checked stuff in

        # Check the repo out somewhere else
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
        b1.FORCE_BUILD = True  # Force a build

        # Add something to the end of the file to cause a collision
        a = AddressRecord.objects.create(
            label="zeenada", domain=root_domain, ip_type='4',
            ip_str='255.0.0.0'
        )
        a.views.add(View.objects.get(name='public'))

        # We should have conflicts here. See if we detect it by
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

    def test_orphan_soa(self):
        SOA.objects.create(
            primary='foo.foo', contact='foo.foo', description='SOA for testing'
        )
        b1 = DNSBuilder(STAGE_DIR=self.stage_dir, PROD_DIR=self.prod_dir,
                        LOCK_FILE=self.lock_file, LOG_SYSLOG=False,
                        FIRST_RUN=True, PUSH_TO_PROD=True,
                        STOP_UPDATE_FILE=self.stop_update)
        b1.build_dns()

    def svn_info(self):
        command_str = "svn info {0}".format(self.prod_dir)
        rets = subprocess.Popen(shlex.split(command_str),
                                stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE)
        stdout, stderr = rets.communicate()
        self.assertEqual(0, rets.returncode)

    def test_build_svn(self):
        print "This will take a while, be patient..."
        b = DNSBuilder(STAGE_DIR=self.stage_dir, PROD_DIR=self.prod_dir,
                       LOCK_FILE=self.lock_file, LOG_SYSLOG=False,
                       FIRST_RUN=True, PUSH_TO_PROD=True)
        b.build_dns()
        #self.svn_info()
        s = SOA.objects.all()
        if len(s) > 0:
            s[0].dirty = True
            s[0].save()
        b.build_dns()
        #self.svn_info()
        b.build_dns()
        #self.svn_info()

    def test_svn_lines_changed(self):
        pass

    def test_build_staging(self):
        if os.path.isdir(self.stage_dir):
            shutil.rmtree(self.stage_dir)
        b = DNSBuilder(STAGE_DIR=self.stage_dir, PROD_DIR=self.prod_dir,
                       LOCK_FILE=self.lock_file)
        b.build_staging()
        # Make sure it made the staging dir
        self.assertTrue(os.path.isdir(self.stage_dir))
        # Ensure if fails if the directory exists
        self.assertRaises(BuildError, b.build_staging)
        # There shouldn't be errors because force=True
        b.build_staging(force=True)

        self.assertTrue(os.path.isdir(self.stage_dir))
        b.clear_staging()
        self.assertFalse(os.path.isdir(self.stage_dir))
        self.assertRaises(BuildError, b.clear_staging)
        b.clear_staging(force=True)
        self.assertFalse(os.path.isdir(self.stage_dir))

    def test_lock_unlock(self):
        if os.path.exists(self.lock_file):
            os.remove(self.lock_file)
        b1 = DNSBuilder(STAGE_DIR=self.stage_dir, PROD_DIR=self.prod_dir,
                        LOCK_FILE=self.lock_file)
        b2 = DNSBuilder(STAGE_DIR=self.stage_dir, PROD_DIR=self.prod_dir,
                        LOCK_FILE=self.lock_file)
        b3 = DNSBuilder(STAGE_DIR=self.stage_dir, PROD_DIR=self.prod_dir,
                        LOCK_FILE=self.lock_file)
        self.assertFalse(os.path.exists(self.lock_file))
        self.assertTrue(b1.lock())
        self.assertTrue(os.path.exists(self.lock_file))
        self.assertTrue(b1.unlock())

        self.assertTrue(b1.lock())
        self.assertFalse(b2.lock())
        self.assertFalse(b2.lock())
        self.assertTrue(b1.unlock())

        self.assertTrue(b2.lock())
        self.assertFalse(b1.lock())
        self.assertTrue(b2.unlock())

        self.assertTrue(b3.lock())
        self.assertFalse(b1.lock())
        self.assertFalse(b2.lock())
        self.assertFalse(b1.unlock())
        self.assertFalse(b2.unlock())
        self.assertTrue(b3.unlock())

        self.assertTrue(b1.lock())
        self.assertTrue(b1.unlock())

    def test_stop_update(self):
        if os.path.exists(self.stop_update):
            os.remove(self.stop_update)
        b = DNSBuilder(STAGE_DIR=self.stage_dir, PROD_DIR=self.prod_dir,
                       LOCK_FILE=self.lock_file,
                       STOP_UPDATE_FILE=self.stop_update)
        open(self.stop_update, 'w+').close()
        try:
            self.assertTrue(b.stop_update_exists())
        finally:
            os.remove(self.stop_update)

    def test_sanity_checks(self):
        b = DNSBuilder(STAGE_DIR=self.stage_dir, PROD_DIR=self.prod_dir,
                       LOCK_FILE=self.lock_file,
                       STOP_UPDATE_FILE=self.stop_update)
        with open(self.re_test_file, 'w+') as fd:
            fd.write("mozilla.com.   IN  A   120.1.1.1")

        SANITY_CHECKS = [
            (self.re_test_file, (
                (r'^mozilla\.com\.\s+(\d+\s+)?IN\s+A\s+'),
            )),
        ]
        b.re_sanity_check(SANITY_CHECKS)

        with open(self.re_test_file, 'w+') as fd:
            fd.write("foo.com.   IN  A   120.1.1.1")

        self.assertRaises(BuildError, b.re_sanity_check, SANITY_CHECKS)
