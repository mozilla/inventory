import os
import sys
import shutil
import pdb

from unittest import TestCase
from scripts.dnsbuilds.main import DNSBuilder, BuildError

import pdb

class BuildScriptTests(TestCase):
    """These test cases test the build scripts and should be able to run
    outside of the django test runner. No checkins should happen during any
    test.
    """

    def setUp(self):
        self.stage_dir = '/tmp/fake/stage/inv_zones/'
        self.svn_dir = '/tmp/fake/dnsconfig/inv_zones/'
        self.lock_file = '/tmp/lock.fake'
        if os.path.isdir('/tmp/fake'):
            shutil.rmtree('/tmp/fake')

    def test_build_staging(self):
        if os.path.isdir(self.stage_dir):
            shutil.rmtree(self.stage_dir)
        b = DNSBuilder(STAGE_DIR=self.stage_dir, PROD_DIR=self.svn_dir,
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
        b = DNSBuilder(STAGE_DIR=self.stage_dir, PROD_DIR=self.svn_dir,
                       LOCK_FILE=self.lock_file)
        self.assertRaises(BuildError, b.unlock)
        pdb.set_trace()
        self.assertFalse(os.path.exists(self.lock_file))
        b.lock()
        self.assertTrue(os.path.exists(self.lock_file))
        for i in xrange(10):
            b.unlock()
            self.assertFalse(os.path.exists(self.lock_file))
            b.lock()
            self.assertTrue(os.path.exists(self.lock_file))

        b.unlock()
        self.assertFalse(os.path.exists(self.lock_file))

        b.lock()
        self.assertRaises(BuildError, b.lock)
        self.assertTrue(os.path.exists(self.lock_file))

        b.unlock()
        self.assertFalse(os.path.exists(self.lock_file))

    def test_build_run(self):
        """Black box tests for a build run."""
        b = DNSBuilder(STAGE_DIR=self.stage_dir, PROD_DIR=self.svn_dir,
                       LOCK_FILE=self.lock_file)
