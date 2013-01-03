#!/usr/bin/python
import hashlib
import inspect
import shutil
import shlex
import subprocess
import syslog
import os
import pdb
import time

from settings.dnsbuilds import STAGE_DIR, PROD_DIR, LOCK_FILE
from settings.dnsbuilds import NAMED_CHECKZONE_OPTS


from mozdns.domain.models import SOA
from mozdns.mozbind.build import build_zone_data
from mozdns.mozbind.models import DNSBuildRun
from mozdns.mozbind.serial_utils import get_serial

class BuildError(Exception):
    """Exception raised when there is an error in the build process."""


class DNSBuilder(object):
    def __init__(self, **kwargs):
        defaults = {
            'STAGE_DIR': STAGE_DIR,
            'PROD_DIR': PROD_DIR,
            'LOCK_FILE': LOCK_FILE,
            'STAGE_ONLY': False,
            'NAMED_CHECKZONE_OPTS': NAMED_CHECKZONE_OPTS,
            'CLOBBER_STAGE': False,
            'PUSH_TO_PROD': False,
            'BUILD_ZONES': True,
            'PRESERVE_STAGE': False,
            'LOG_SYSLOG': True,
            'DEBUG': False,
            'MAX_ALLOWED_LINES_CHANGED': 500,
            'bs': DNSBuildRun()  # Build statistic
        }
        for k, default in defaults.iteritems():
            setattr(self, k, kwargs.get(k, default))

        # This is very specific to python 2.6
        syslog.openlog('dnsbuild', 0, syslog.LOG_USER)

    def log(self, log_level, msg, **kwargs):
        # Eventually log this stuff into bs
        # Let's get the callers name and log that
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        callername = calframe[1][3]
        fmsg = "[{0}] {1}".format(callername, msg)
        if hasattr(syslog, log_level):
            ll = getattr(syslog, log_level)
        else:
            ll = syslog.LOG_INFO

        if self.LOG_SYSLOG:
            syslog.syslog(ll, fmsg)
        if self.DEBUG:
            print "{0} {1}".format(log_level, fmsg)

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
        except OSError:
            if not force:
                raise


    def clear_staging(self, force=False):
        """
        rm -rf the staging area. Fail if the staging area doesn't exist.
        """
        self.log('LOG_INFO', "Attempting rm -rf staging "
                 "area. ({0})...".format(self.STAGE_DIR))
        if os.path.exists(self.STAGE_DIR) or force:
            try:
                shutil.rmtree(self.STAGE_DIR)
            except OSError, e:
                if e.errno == 2:
                    self.log('LOG_WARNING', "Staging was "
                             "not present.")
                else:
                    raise
            self.log('LOG_INFO', "Staging area cleared")
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
                             "file but another lock file was already in place.")
        lock_dir = os.path.dirname(self.LOCK_FILE)
        if not os.path.exists(lock_dir):
            os.makedirs(lock_dir)
        self.log('LOG_INFO', "Attempting write lock "
                              "({0})...".format(self.LOCK_FILE))
        with open(self.LOCK_FILE, 'w+') as lock:
            lock.write("{0} # DO NOT TOUCH THE CONTENTS OF THIS "
                       "FILE!\n".format(time.time()))
        self.log('LOG_INFO', "Lock written.")

    def unlock(self):
        """
        Try to remove the lock file. Fail very loudly if the lock doesn't exist
        and this function is called.
        """
        if not os.path.isfile(self.LOCK_FILE):
            raise BuildError("DNS build script attemted to unlock but no lock "
                             "file was found.")
        self.log('LOG_INFO', "Attempting Unlock "
                              "({0})...".format(self.LOCK_FILE))
        os.remove(self.LOCK_FILE)
        self.log('LOG_INFO', "Unlock Complete.")


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
        self.log('LOG_INFO', "Stage zone file is {0}".format(stage_zone_file),
                soa=soa)
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
        self.log('LOG_INFO', "Calling `named-checkzone '{0}' "
                             "'{1}'".format(root_domain.name, zone_file))
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
        self.log('LOG_INFO', "Calling `named-checkconf {0}` ".
                                   format(conf_file))
        stdout, stderr, returncode = self._shell_out(command_str)
        if returncode != 0:
            raise BuildError("\nnamed-checkconf rejected config {0}. "
                             "\ncommand: {1}:\nstdout: {2}\nstderr:{3}".
                             format(conf_file, command_str, stdout,
                             stderr))

    def stage_to_prod(self, src):
        """Copy file over to PROD_DIR. Return the new location of the
        file.
        """

        if not src.startswith(self.STAGE_DIR):
            raise BuildError("Improper file '{0}' passed to "
                             "stage_to_prod".format(src))
        dst = src.replace(self.STAGE_DIR, self.PROD_DIR)
        dst_dir = os.path.dirname(dst)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        # copy2 will copy file metadata
        try:
            shutil.copy2(src, dst)
            self.log('LOG_INFO', "Copied {0} to {1}".format(src, dst))
        except (IOError, os.error) as why:
            raise BuildError("cp -p {0} {1} caused {2}".format(src,
                             dst, str(why)))
        except shutil.Error:
            pdb.set_trace()
        return dst



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

    def rebuild_zone(self, private_data, public_data, root_domain, soa):
        """
        This function will write the zone's zone file to the the staging area
        and call named-checkconf on the files before they are copied over to
        PROD_DIR. If will return a tuple of files corresponding to where the
        `privat_file` and `public_file` are written to. If a file is not
        written to the file system `None` will be returned instead of the path
        to the file.
        """
        self.log('LOG_INFO', "{0} will be rebuilt.".format(soa))
        t_start = time.time()  # tic
        build_time = time.time() - t_start  # toc
        self.log('LOG_INFO', 'Built {0} in {1} seconds '.format(soa,
                 build_time), soa=soa, build_time=build_time)

        # write datas to files (in stage) and named-checkzone
        private_file, public_file = None, None
        if private_data:
            fname = "{0}.{1}".format(root_domain.name, 'private')
            private_file = self.write_stage_zone(root_domain, soa, fname,
                                                       private_data)
            self.log('LOG_INFO', "Built stage_private_file to "
                     "{0}".format(private_file))
            self.named_checkzone(private_file, root_domain, soa)

        if public_data:
            fname = "{0}.{1}".format(root_domain.name, 'public')
            public_file = self.write_stage_zone(root_domain, soa, fname,
                                                       public_data)
            self.log('LOG_INFO', "Built stage_public_file to "
                     "{0}".format(public_file))
            self.named_checkzone(public_file, root_domain, soa)

        # cp over
        if private_file:
            private_file = self.stage_to_prod(private_file)

        if public_file:
            public_file = self.stage_to_prod(public_file)

        return private_file, public_file

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

    def verify_prev(self, prev_run, private_info, public_info, zhash,
                    root_domain, soa):
        for zfile, zdata in (private_info, public_info):
            if not zdata:
                continue
            serial = get_serial(os.path.join(self.PROD_DIR, zfile))
            if not serial:
                if not soa.serial:
                    soa.serial = int(time.time())
                soa.serial
                soa.dirty = True
                # it's a new serial
                self.log('LOG_NOTICE', "{0} appears to be a new zone. Building"
                         " {1} with initial serial {2}".format(soa, zfile,
                         soa.serial), soa=soa)
            elif int(serial) != soa.serial:
                # Looks like someone made some changes... let's nuke them.
                # We should probably email someone too.
                self.log('LOG_NOTICE', "{0} has serial {1} in svn ({2}) and "
                         "serial {3} in the database. SOA is being marked as "
                         "dirty.".format(soa, serial, zfile, soa.serial),
                         soa=soa)
                soa.serial = int(serial)
                soa.dirty = True

    def build_zone_files(self):
        """
        This function builds and then writes zone files to the file system.
        This function also returns a list of zone statements.
        """

        # Keep track of which zones we build and what they look like.

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
            # We build the *_data here. If either private_data or public_data
            # is '', that means we don't have to worry about it. There was a
            # small bug with having it built in :func:`rebuild_zone`:: if
            # either the public or private file had data in it then for some
            # reason the zone didn't have data for that file anymore, the file
            # wouldn't get written. The problem was that the serial in the
            # unused file wasn't being changed which caused the zone to always
            # be marked as dirty in :func:`verify_prev`. Passing the *_data
            # variables to :func:`verify_prev` will allow us to avoid checking
            # the stale files. Eventually, we should look into deleteing the
            # unused files.
            private_data, public_data = build_zone_data(*zinfo)

            zhash = self._calc_build_hash(zfiles)
            # If there is zomething different about the zone, mark the soa as
            # dirty.
            self.verify_prev(prev_run, (zfiles[0], private_data), (zfiles[1],
                             public_data), zhash, *zinfo)
            if soa.dirty:
                self.log('LOG_INFO', "{0} is seen as dirty.".format(soa),
                         soa=soa)
                soa.serial += 1
                self.log('LOG_INFO', "{0} incremented serial from {1} to "
                         "{2}".format(soa, soa.serial - 1, soa.serial), soa=soa)
                zfiles = self.rebuild_zone(private_data, public_data, *zinfo)
            else:
                # Everything is being marked as dirty, wtf?
                self.log('LOG_INFO', "{0} is seen as NOT dirty.".format(soa),
                         soa=soa)
                if private_data:
                    self.named_checkzone(os.path.join(self.PROD_DIR, zfiles[0]),
                                         *zinfo)
                if public_data:
                    self.named_checkzone(os.path.join(self.PROD_DIR, zfiles[1]),
                                         *zinfo)

            if zfiles[0]:
                private_zone_stmts.append(
                    self.render_zone_stmt(zinfo[0].name,
                                os.path.join(self.PROD_DIR, zfiles[0])))
            if zfiles[1]:
                public_zone_stmts.append(
                    self.render_zone_stmt(zinfo[0].name,
                                os.path.join(self.PROD_DIR, zfiles[1])))

            if soa.dirty: # we made it through the build successfully
                self.log('LOG_INFO', "Marking {0} as NOT dirty.".format(soa),
                         soa=soa)
                soa.dirty = False
                self.log('LOG_INFO', "Saving {0}".format(soa), soa=soa)
                soa.save()

        return private_zone_stmts, public_zone_stmts

    def build_config_files(self, private_zone_stmts, public_zone_stmts):
        # named-checkconf on config files
        self.log('LOG_INFO', "Building config files.")
        for type_ in ('master',): # If we need slave configs, do it here
            zone_stmts = '\n'.join(private_zone_stmts).format(type_=type_)
            stage_private_file = self.write_stage_config(
                                    '{0}.private'.format(type_), zone_stmts)
            self.named_checkconf(stage_private_file)
            self.stage_to_prod(stage_private_file)

            zone_stmts = '\n'.join(public_zone_stmts).format(type_=type_)
            stage_public_file = self.write_stage_config(
                                    '{0}.public'.format(type_), zone_stmts)
            self.named_checkconf(stage_public_file)
            self.stage_to_prod(stage_public_file)

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

    def rcs_checkin(self):
        """TODO write a mixin class for svn."""
        return

    def build_dns(self):
        self.log('LOG_NOTICE', 'Building...')
        try:
            self.lock()
        except BuildError, e:
            raise BuildError("There is probably another instance of the build "
                             "script running")
            return

        try:
            if self.CLOBBER_STAGE:
                self.clear_staging(force=True)
            self.build_staging()

            # zone files
            if self.BUILD_ZONES:
                self.build_config_files(*self.build_zone_files())
            else:
                self.log('LOG_INFO', "BUILD_ZONES is False. Not "
                         "building zone files.")
            # Run sanity checks
            self.sanity_check()
            if self.BUILD_ZONES and self.PUSH_TO_PROD:
                self.log('LOG_INFO', "PUSH_TO_PROD is True. Checking into "
                         "rcs.")
                self.rcs_checkin()
            else:
                self.log('LOG_INFO', "PUSH_TO_PROD is False. Not checking "
                         "into rcs.")
            if self.PRESERVE_STAGE:
                self.log('LOG_INFO', "PRESERVE_STAGE is True. Not "
                         "removing staging. You will need to use "
                         "--clobber-stage on the next run.")
            else:
                self.clear_staging()
        # All errors are handled by caller
        except BuildError, e:
            self.log('LOG_NOTICE', 'Error during build. Not removing staging')
            raise
        except Exception, e:
            print e
            self.log('LOG_NOTICE', 'Error during build. Not removing staging')
            raise
        finally:
            # Clean up
            self.unlock()
        self.log('LOG_NOTICE', 'Successful build is successful.')
