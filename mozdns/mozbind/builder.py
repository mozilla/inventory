#!/usr/bin/python
import shutil
import shlex
import subprocess
import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                        os.pardir, os.pardir)))
import manage
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.base'
from settings.dnsbuilds import STAGE_DIR, PROD_DIR, LOCK_FILE
from settings.dnsbuilds import NAMED_CHECKZONE_OPTS

import pdb

from mozdns.domain.models import SOA
from mozdns.mozbind.build import build_zone_data
from mozdns.mozbind.models import DNSBuildRun

class BuildError(Exception):
    """Exception raised when there is an error in the build process."""


class DNSBuilder(object):
    def __init__(self, STAGE_DIR=STAGE_DIR, PROD_DIR=PROD_DIR,
                 LOCK_FILE=LOCK_FILE, RO=False,
                 NAMED_CHECKZONE_OPTS=NAMED_CHECKZONE_OPTS):
        self.RO=RO
        self.STAGE_DIR=STAGE_DIR
        self.PROD_DIR=PROD_DIR
        self.LOCK_FILE=LOCK_FILE
        self.bs = DNSBuildRun()
        self.MAX_ALLOWED_LINES_CHANGED = 500
        self.NAMED_CHECKZONE_OPTS = NAMED_CHECKZONE_OPTS

    def log(self, soa, k, v):
        # Eventually log this stuff into bs
        """
        """
        print "[{0}] --> {1}: {2}".format(soa, k, v)

    def build_staging(self, force=False):
        """
        Create the stage folder. Fail if it already exists unless
        force=True.
        """
        if os.path.exists(self.STAGE_DIR) and not force:
            raise BuildError("The DNS build scripts tried to build the staging"
                             " but area already exists.")
        try:
            os.makedirs(self.STAGE_DIR)
        except OSError, e:
            if not force:
                raise


    def clear_staging(self, force=False):
        """
        rm -rf the staging area. Fail if the staging area doesn't exist.
        """
        self.log('BUILD CLEAR STAGE', 'info', "Attempting rm -rf staging area."
                              "({0})...".format(self.LOCK_FILE))
        if os.path.exists(self.STAGE_DIR) or force:
            shutil.rmtree(self.STAGE_DIR)
            self.log('BUILD CLEAR STAGE', 'info', "Staging area cleared")
        else:
            if not force:
                raise BuildError("The DNS build scripts tried to remove the "
                                 "staging area but the staging area didn't "
                                 "exist.")

    def lock(self):
        """
        Try to write a lock file. Fail if the lock already exists.
        """
        if os.path.isfile(self.LOCK_FILE):
            raise BuildError("DNS build script attemted to write it's lock "
                             "file but another lock file was already in place")
        lock_dir = os.path.dirname(self.LOCK_FILE)
        if not os.path.exists(lock_dir):
            os.makedirs(lock_dir)
        self.log('BUILD LOCK', 'info', "Attempting write lock "
                              "({0})...".format(self.LOCK_FILE))
        with open(self.LOCK_FILE, 'w+') as lock:
            lock.write("{0} # DO NOT TOUCH THE CONTENTS OF THIS "
                       "FILE!\n".format(time.time()))
        self.log('BUILD_LOCK', 'info', "Lock written.")

    def unlock(self):
        """
        Try to remove the lock file. Fail very loudly if the lock doesn't exist
        and this function is called.
        """
        if not os.path.isfile(self.LOCK_FILE):
            raise BuildError("DNS build script attemted to unlock but no lock "
                             "file was found.")
        self.log('UNLOCK', 'info', "Attempting Unlock "
                              "({0})...".format(self.LOCK_FILE))
        os.remove(self.LOCK_FILE)
        self.log('UNLOCK', 'info', "Unlock Complete.")

    def ensure_build_keys(self, soa):
        """
        Make sure that key's _private_zone_file and _public_zone_file exist.
        If they don't exist or if the files that the key's point to do not
        exist, mark the soa to be rebuilt.
        """
        if not soa.attrs:
            raise BuildError("You called calc_target without calling "
                             "update_attrs on the soa.")
        if not (hasattr(soa.attrs, '_private_zone_file') and
           os.path.exists(soa.attrs._private_zone_file) and
           hasattr(soa.attrs, '_public_zone_file') and
           os.path.exists(soa.attrs._public_zone_file)):
            soa.dirty = True
            soa.save()


    def check_for_manual_changes(self, soa):
        """
        Shell out and run some svn commands on _private_zone_file and
        _public_zone_file.
        :returns changed: If someone clobbered the file, return True. No
            changes means False
        :type changed: bool
        """
        # How do we do this?
        return False

    def calc_target(self, root_domain, soa):
        """
        .. warning::

            The whole `zone_path` key thing isn't implemented yet.

        This function decides which directory a zone's zone files go. If there
        is a key in the zone's KeyValue store called 'zone_path', that path is
        used. The path contained in 'zone_path' must exist on the file system
        or the default path is calculated.

        If no zone_path key is found. The following is used to decide on the
        target directory.

        If `root_domain` is a forward domain:

            * Replace all '.' characters with '/' characters.

        If `root_domain` is a reverse domain:

            If it's ipv4:

                'reverse/in-addr.arpa/'
            If it's ipv6:

                'reverse/in-addr.ipv6/'

        The build scripts will create this path on the filesystem if it does
        not exist.

        .. note::

            In cases that the `zone_path` key is used, it is used as an
            absolute path. Other cases are calculated as a relative path.
        """
        if root_domain.is_reverse:
            if root_domain.name.endswith('ipv6'):
                zone_path = "reverse/in-addr.arpa/"
            elif root_domain.name.endswith('arpa'):
                zone_path = "reverse/in-addr.arpa/"
            else:
                raise Exception("WTF type of reverse domain is this "
                        "{0}?!?".format(root_domain))
        else:
            tmp_path = '/'.join(reversed(root_domain.name.split('.')))
            zone_path = tmp_path + '/'
        return zone_path

    def write_stage_zone(self, root_domain, soa, fname, data):
        """
        Write a zone_file.
        Return the path to the file.
        """
        stage_zone_dir = os.path.join(self.STAGE_DIR,
                                      self.calc_target(root_domain, soa))
        if not os.path.exists(stage_zone_dir):
            os.makedirs(stage_zone_dir)
        stage_zone_file = os.path.join(stage_zone_dir, fname)
        self.log(soa, 'info', "Stage zone file is {0}".format(stage_zone_file))
        if not self.RO:
            with open(stage_zone_file, 'w+') as fd:
                fd.write(data)
        return stage_zone_file

    def _shell_out(self, command):
        """A little helper function that will shell out and return stdout,
        stderr and the return code."""
        p = subprocess.Popen(shlex.split(command),
                             stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        return stdout, stderr, p.returncode

    def named_checkzone(self, zone_file, root_domain, soa):
        """Shell out and call named-checkzone on the zone file. If it returns
        with errors raise a BuildError.
        """
        # Make sure we have the write tools to do the job
        command_str = "which named-checkzone"
        stdout, stderr, returncode = self._shell_out(command_str)
        if returncode != 0:
            raise BuildError("Couldn't find named-checkzone.")

        # Check the zone file.
        command_str = "named-checkzone {0} {1} {2}".format(
                      self.NAMED_CHECKZONE_OPTS, root_domain.name,
                      zone_file)
        self.log('VERIFY', 'info', "Calling named-checkzone on zone '{0}' with "
                                   "zone file {1}".format(root_domain.name,
                                   zone_file))
        stdout, stderr, returncode = self._shell_out(command_str)
        if returncode != 0:
            raise BuildError("\nnamed-checkzone failed on zone {0}. "
                             "\ncommand: {1}:\nstdout: {2}\nstderr:{3}".
                             format(root_domain.name, command_str, stdout,
                             stderr))

    def named_checkconf(self, conf_file):
        command_str = "which named-checkconf"
        stdout, stderr, returncode = self._shell_out(command_str)
        if returncode != 0:
            raise BuildError("Couldn't find named-checkconf.")

        command_str = "named-checkconf {0}".format(conf_file)
        self.log('VERIFY', 'info', "Calling named-checkconf {0}' ".
                                   format(conf_file))
        stdout, stderr, returncode = self._shell_out(command_str)
        if returncode != 0:
            raise BuildError("\nnamed-checkconf rejected config {0}. "
                             "\ncommand: {1}:\nstdout: {2}\nstderr:{3}".
                             format(conf_file, command_str, stdout,
                             stderr))

    def stage_to_prod(self, files):
        """Copy files over to PROD_DIR. Return the new location of the zone
        files.
        """
        # TODO
        return [fname.replace(self.STAGE_DIR, self.PROD_DIR)
                for fname in files]

    def write_stage_config(self, fname, data):
        """
        Write config files to the correct area in staging.
        Return the path to the file.
        """
        config_path = os.path.join(self.STAGE_DIR, "config/")
        if not os.path.exists(config_path):
            os.makedirs(config_path)
        config_file = os.path.join(config_path, fname)
        with open(config_file, 'w+') as fd:
            fd.write(data)
        return config_file

    def dirty_if_new(self, prev_run, root_domain, soa):
        if soa.dirty:
            return
        # Look at the previous build and determine if we have seen this zone in
        # it's previous configuration. md5sum the zone and compare.

    def _rebuild_zone(self, root_domain, soa):
        """
        This function will write the zone's zone file to the the staging area
        and call named-checkconf on the files before they are copied over to
        PROD_DIR.
        """
        self.log(soa, 'info', "{0} will be rebuilt.".format(soa))
        t_start = time.time()  # tic
        public_data, private_data = build_zone_data(root_domain, soa)
        build_time = time.time() - t_start  # toc
        self.log(soa, 'build_time_seconds', build_time)

        # write datas to files (in stage) and named-checkzone
        stage_files = []
        if private_data:
            fname = "{0}.{1}".format(root_domain.name, 'private')
            stage_private_file = self.write_stage_zone(root_domain, soa, fname,
                                                       private_data)
            stage_files.append(stage_private_file)
            self.log(soa, 'info', "Built stage_private_file to "
                     "{0}".format(stage_private_file))
            self.named_checkzone(stage_private_file, root_domain, soa)
        else:
            stage_private_file = None

        if public_data:
            fname = "{0}.{1}".format(root_domain.name, 'public')
            stage_public_file = self.write_stage_zone(root_domain, soa, fname,
                                                       public_data)
            stage_files.append(stage_public_file)
            self.log(soa, 'info', "Built stage_public_file to "
                     "{0}".format(stage_public_file))
            self.named_checkzone(stage_public_file, root_domain, soa)
        else:
            stage_public_file = None

        # cp over (not new file for later svn ci)
        self.stage_to_prod(stage_files)
        return stage_private_file, stage_public_file

    def calc_fnames(self, root_domain, soa):
        return ("{0}.{1}".format(root_domain.name, 'private'),
                "{0}.{1}".format(root_domain.name, 'public'))

    def _calc_build_hash(self, files):
        """Given a list of files, hash them and return the hex digest of the
        hash. If this function fails to open on of the files it will return
        None."""
        hashables = ""
        for file_ in files:
            try:
                hashables += open(file_, 'r').read()
            except IOError:
                return None
        return hashlib.md5(hashables).hexdigest()

    def render_zone_stmt(self, zone_name, file_path):
        zone_stmt = "zone \"{0}\" IN {{{{\n".format(zone_name)
        zone_stmt += "\ttype {type_};\n"  # We'll format this later
        zone_stmt += "\tfile \"{0}\";\n".format(file_path)
        zone_stmt += "}};\n"
        return zone_stmt

    def get_prev(self):
        """Get the previous DNSBuildRun instance."""
        return None

    def verify_prev(self, prev_run, zfiles, zhash, root_domain, soa):
        if not prev_run:
            soa.dirty = True  # It's a local copy, we we don't need to save it.
        return None

    def build_zone_files(self):
        """
        This function builds and then writes zone files to the file system.
        This function also returns a list of zone statements.
        """
        # Keep track of which zones we build and what they look like.
        build_manifest = []

        private_zone_stmts, public_zone_stmts = [], []

        for soa in SOA.objects.all():
            zinfo = soa.root_domain, soa
            prev_run = self.get_prev()
            # If someone has made manual changes to the zone files we must flag
            # the soa as dirty and email a warning.
            # Something is different. Let's nuke the change.
            zdir = self.calc_target(*zinfo)
            fnames = self.calc_fnames(*zinfo)
            zfiles = [os.path.join(zdir, fname) for fname in fnames]
                    # zfiles[0] -> private_zone_file
                    # zfiles[1] -> public_zone_file
            zhash = self._calc_build_hash(zfiles)
            # Pretty sure all new SOA's are marked as dirty but let's be
            # paranoid.
            self.dirty_if_new(prev_run, *zinfo)
            # If there is zomething different about the zone, mark the soa as
            # dirty.
            self.verify_prev(prev_run, zfiles, zhash, *zinfo)
            if soa.dirty:
                zfiles = self._rebuild_zone(*zinfo)
            else:
                self.named_checkzone(zfiles[0], *zinfo)
                self.named_checkzone(zfiles[1], *zinfo)

            if zfiles[0]:
                private_zone_stmts.append(
                    self.render_zone_stmt(zinfo[0].name, zfiles[0]))
            if zfiles[1]:
                public_zone_stmts.append(
                    self.render_zone_stmt(zinfo[0].name, zfiles[1]))

        return private_zone_stmts, public_zone_stmts

    def build_config_files(self, private_zone_stmts, public_zone_stmts):
        # named-checkconf on config files
        self.log('CONFIG BUILD', 'info', "Building config files.")
        for type_ in ('master',): # If we need slave configs, do it here
            zone_stmts = '\n'.join(private_zone_stmts).format(type_=type_)
            stage_private_file = self.write_stage_config(
                                    '{0}.private'.format(type_), zone_stmts)
            self.named_checkconf(stage_private_file)
            private_file = self.stage_to_prod(stage_private_file)

            zone_stmts = '\n'.join(public_zone_stmts).format(type_=type_)
            stage_public_file = self.write_stage_config(
                                    '{0}.public'.format(type_), zone_stmts)
            self.named_checkconf(stage_public_file)
            public_file = self.stage_to_prod(stage_public_file)

    def _lines_changed(self):
        return 0

    def sanity_check(self):
        """If sanity checks fail, this function will return a string which is
        True-ish. If all sanity cheecks pass, a Falsy value will be
        returned."""
        # svn diff changes and react if changes are too large
        if self._lines_changed() > self.MAX_ALLOWED_LINES_CHANGED:
            pass
        # email and fail
            # Make sure we can run the script again
            # rm -rf stage/
            # rm lock.file
        return False

    def build_dns(self):
        try:
            self.lock()
            self.build_staging()

            # zone files
            self.build_config_files(*self.build_zone_files())
            # Run sanity checks
            self.sanity_check()
            self.clear_staging()

        except BuildError, e:
            self.log('BUILD MAIN', 'info', 'Not removing staging')
            print e
            raise
        except Exception, e:
            self.log('BUILD MAIN', 'info', 'Not removing staging')
            print e
            raise
        finally:
            # Clean up
            self.unlock()
