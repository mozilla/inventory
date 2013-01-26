#!/usr/bin/python
from gettext import gettext as _
import inspect
import fcntl
import shutil
import shlex
import subprocess
import syslog
import os
import re
import time

from settings.dnsbuilds import STAGE_DIR, PROD_DIR, LOCK_FILE, STOP_UPDATE_FILE
from settings.dnsbuilds import NAMED_CHECKZONE_OPTS, MAX_ALLOWED_LINES_CHANGED

from mozdns.domain.models import SOA
from mozdns.view.models import View
from mozdns.mozbind.zone_builder import build_zone_data
from mozdns.mozbind.models import DNSBuildRun
from mozdns.mozbind.serial_utils import get_serial


class BuildError(Exception):
    """Exception raised when there is an error in the build process."""


class SVNBuilderMixin(object):
    svn_ignore = [re.compile("---\s.+\s+\(revision\s\d+\)"),
                  re.compile("\+\+\+\s.+\s+\(working copy\)")]

    vcs_type = 'svn'

    def svn_lines_changed(self):
        """This function will collect some metrics on how many lines were added
        and removed during the build process.

        :returns: (int, int) -> (lines_added, lines_removed)

        The current implementation of this function uses the underlying svn
        repo to generate a diff and then counts the number of lines that start
        with '-' or '+'. This causes the accuracy of this function to have
        slight errors because some lines in the diff output start with '-' or
        '+' but aren't indicative of a line being removed or added. Since the
        threashold of lines changing is in the hundreds of lines, an error of
        tens of lines is not a large concern.
        """
        cwd = os.getcwd()
        os.chdir(self.PROD_DIR)
        try:
            command_str = "svn add --force .".format(self.PROD_DIR)
            stdout, stderr, returncode = self.shell_out(command_str)
            if returncode != 0:
                raise BuildError("\nFailed to add files to svn."
                                 "\ncommand: {0}:\nstdout: {1}\nstderr:{2}".
                                 format(command_str, stdout, stderr))
            command_str = "svn diff --depth=infinity ."
            stdout, stderr, returncode = self.shell_out(command_str)
            if returncode != 0:
                raise BuildError("\nFailed to add files to svn."
                                 "\ncommand: {0}:\nstdout: {1}\nstderr:{2}".
                                 format(command_str, stdout, stderr))
        except Exception:
            raise
        finally:
            os.chdir(cwd)  # go back!

        la, lr = 0, 0

        def svn_ignore(line):
            for ignore in self.svn_ignore:
                if ignore.match(line):
                    return True
            return False
        for line in stdout.split('\n'):
            if svn_ignore(line):
                continue
            if line.startswith('-'):
                lr += 1
            elif line.startswith('+'):
                la += 1
        return la, lr

    def svn_sanity_check(self, lines_changed):
        """If sanity checks fail, this function will return a string which is
        True-ish. If all sanity cheecks pass, a Falsy value will be
        returned."""
        # svn diff changes and react if changes are too large
        if ((lambda x, y: x + y)(*lines_changed) >
                MAX_ALLOWED_LINES_CHANGED):
            raise BuildError("Wow! Too many lines changed during this "
                             "checkin. {0} lines add, {1} lines removed."
                             .format(**lines_changed))

    def svn_checkin(self, lines_changed):
        # svn add has already been called
        cwd = os.getcwd()
        os.chdir(self.PROD_DIR)
        self.log('LOG_INFO', "Changing pwd to {0}".format(self.PROD_DIR))
        try:
            """
            command_str = "svn add --force .".format(self.PROD_DIR)
            stdout, stderr, returncode = self.shell_out(command_str)
            if returncode != 0:
                raise BuildError("\nFailed to add files to svn."
                                 "\ncommand: {0}:\nstdout: {1}\nstderr:{2}".
                                 format(command_str, stdout, stderr))
            """

            ci_message = _("Checking in DNS. {0} lines were added and {1} were"
                           " removed".format(*lines_changed))
            self.log('LOG_INFO', "Commit message: {0}".format(ci_message))
            command_str = "svn ci {0} -m \"{1}\"".format(
                self.PROD_DIR, ci_message)
            stdout, stderr, returncode = self.shell_out(command_str)
            if returncode != 0:
                raise BuildError("\nFailed to check in changes."
                                 "\ncommand: {0}:\nstdout: {1}\nstderr:{2}".
                                 format(command_str, stdout, stderr))
            else:
                self.log('LOG_INFO', "Changes have been checked in.")
        finally:
            os.chdir(cwd)  # go back!
            self.log('LOG_INFO', "Changing pwd to {0}".format(cwd))
        return

    def vcs_checkin(self):
        lines_changed = self.svn_lines_changed()
        self.svn_sanity_check(lines_changed)
        if lines_changed == (0, 0):
            self.log('LOG_INFO', "PUSH_TO_PROD is True but "
                     "svn_lines_changed found that no lines different "
                     "from last svn checkin.")
        else:
            self.log('LOG_INFO', "PUSH_TO_PROD is True. Checking into "
                     "svn.")
            self.svn_checkin(lines_changed)


class DNSBuilder(SVNBuilderMixin):
    def __init__(self, **kwargs):
        defaults = {
            'STAGE_DIR': STAGE_DIR,
            'PROD_DIR': PROD_DIR,
            'LOCK_FILE': LOCK_FILE,
            'STOP_UPDATE_FILE': STOP_UPDATE_FILE,
            'STAGE_ONLY': False,
            'NAMED_CHECKZONE_OPTS': NAMED_CHECKZONE_OPTS,
            'CLOBBER_STAGE': False,
            'PUSH_TO_PROD': False,
            'BUILD_ZONES': True,
            'PRESERVE_STAGE': False,
            'LOG_SYSLOG': True,
            'DEBUG': False,
            'bs': DNSBuildRun()  # Build statistic
        }
        for k, default in defaults.iteritems():
            setattr(self, k, kwargs.get(k, default))

        # This is very specific to python 2.6
        syslog.openlog('dnsbuild', 0, syslog.LOG_USER)
        self.lock_fd = None

    def format_title(self, title):
        return "{0} {1} {0}".format('=' * ((30 - len(title)) / 2), title)

    def log(self, log_level, msg, **kwargs):
        # Eventually log this stuff into bs
        # Let's get the callers name and log that
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        callername = "[{0}]".format(calframe[1][3])
        soa = kwargs.get('soa', None)
        if soa:
            fmsg = "{0:20} < {1} > {2}".format(callername,
                                               soa.root_domain.name, msg)
        else:
            fmsg = "{0:20} {1}".format(callername, msg)
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
                    self.log('LOG_WARNING', "Staging was not present.")
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
        try:
            if not os.path.exists(os.path.dirname(self.LOCK_FILE)):
                os.makedirs(os.path.dirname(self.LOCK_FILE))
            self.log('LOG_INFO', "Attempting acquire mutext "
                     "({0})...".format(self.LOCK_FILE))
            self.lock_fd = open(self.LOCK_FILE, 'w+')
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.log('LOG_INFO', "Lock written.")
        except IOError, exc_value:
            #  IOError: [Errno 11] Resource temporarily unavailable
            if exc_value[0] == 11:
                raise BuildError(
                    "DNS build script attempted to acquire the "
                    "build mutux but another process already has it.")
            else:
                raise

    def unlock(self):
        """
        Try to remove the lock file. Fail very loudly if the lock doesn't exist
        and this function is called.
        """
        self.log('LOG_INFO', "Attempting release mutex "
                 "({0})...".format(self.LOCK_FILE))
        fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
        self.log('LOG_INFO', "Unlock Complete.")

    def calc_target(self, root_domain, soa):
        """
        This function decides which directory a zone's zone files go. The
        following is used to decide on the target directory.

        If `root_domain` is a forward domain:

            * Replace all '.' characters with '/' characters.

        If `root_domain` is a reverse domain:

            If it's ipv4:

                'reverse/in-addr.arpa/'
            If it's ipv6:

                'reverse/in-addr.ipv6/'

        The build scripts will create this path on the filesystem if it does
        not exist.

        A relative path is returned by this function.
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

    def write_stage_zone(self, stage_fname, root_domain, soa, fname, data):
        """
        Write a zone_file.
        Return the path to the file.
        """
        if not os.path.exists(os.path.dirname(stage_fname)):
            os.makedirs(os.path.dirname(stage_fname))
        self.log('LOG_INFO', "Stage zone file is {0}".format(stage_fname,
                                                             soa=soa))
        with open(stage_fname, 'w+') as fd:
            fd.write(data)
        return stage_fname

    def shell_out(self, command, use_shlex=True):
        """A little helper function that will shell out and return stdout,
        stderr and the return code."""
        if use_shlex:
            command_args = shlex.split(command)
        else:
            command_args = command
        p = subprocess.Popen(command_args, stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        return stdout, stderr, p.returncode

    def named_checkzone(self, zone_file, root_domain, soa):
        """Shell out and call named-checkzone on the zone file. If it returns
        with errors raise a BuildError.
        """
        # Make sure we have the write tools to do the job
        command_str = "which named-checkzone"
        stdout, stderr, returncode = self.shell_out(command_str)
        if returncode != 0:
            raise BuildError("Couldn't find named-checkzone.")

        # Check the zone file.
        command_str = "named-checkzone {0} {1} {2}".format(
                      self.NAMED_CHECKZONE_OPTS, root_domain.name,
                      zone_file)
        self.log(
            'LOG_INFO', "Calling `named-checkzone {0} {1}`".
            format(root_domain.name, zone_file),
            soa=soa
        )
        stdout, stderr, returncode = self.shell_out(command_str)
        if returncode != 0:
            raise BuildError("\nnamed-checkzone failed on zone {0}. "
                             "\ncommand: {1}\nstdout: {2}\nstderr:{3}\n".
                             format(root_domain.name, command_str, stdout,
                             stderr))

    def named_checkconf(self, conf_file):
        command_str = "which named-checkconf"
        stdout, stderr, returncode = self.shell_out(command_str)
        if returncode != 0:
            raise BuildError("Couldn't find named-checkconf.")

        command_str = "named-checkconf {0}".format(conf_file)
        self.log('LOG_INFO', "Calling `named-checkconf {0}` ".
                 format(conf_file))
        stdout, stderr, returncode = self.shell_out(command_str)
        if returncode != 0:
            raise BuildError("\nnamed-checkconf rejected config {0}. "
                             "\ncommand: {1}\nstdout: {2}\nstderr:{3}\n".
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
            raise
        return dst

    def write_stage_config(self, config_fname, stmts):
        """
        Write config files to the correct area in staging.
        Return the path to the file.
        """
        stage_config = os.path.join(self.STAGE_DIR, "config", config_fname)

        if not os.path.exists(os.path.dirname(stage_config)):
            os.makedirs(os.path.dirname(stage_config))
        with open(stage_config, 'w+') as fd:
            fd.write(stmts)
        return stage_config

    def build_zone(self, view, file_meta, view_data, root_domain, soa):
        """
        This function will write the zone's zone file to the the staging area
        and call named-checkconf on the files before they are copied over to
        PROD_DIR. If will return a tuple of files corresponding to where the
        `privat_file` and `public_file` are written to. If a file is not
        written to the file system `None` will be returned instead of the path
        to the file.
        """
        stage_fname = os.path.join(self.STAGE_DIR, file_meta['rel_fname'])
        self.write_stage_zone(
            stage_fname, root_domain, soa, file_meta['rel_fname'], view_data
        )
        self.log('LOG_INFO', "Built stage_{0}_file to "
                             "{1}".format(view.name, stage_fname), soa=soa)
        self.named_checkzone(stage_fname, root_domain, soa)

        prod_fname = self.stage_to_prod(stage_fname)

        return prod_fname

    def calc_fname(self, view, root_domain):
        return "{0}.{1}".format(root_domain.name, view.name)

    def render_zone_stmt(self, zone_name, file_path):
        zone_stmt = "zone \"{0}\" IN {{{{\n".format(zone_name)
        zone_stmt += "\ttype {ztype};\n"  # We'll format this later
        zone_stmt += "\tfile \"{0}\";\n".format(file_path)
        zone_stmt += "}};\n"
        return zone_stmt

    def verify_previous_build(self, file_meta, view, root_domain, soa):
        force_rebuild, new_serial = False, None
        serial = get_serial(os.path.join(file_meta['prod_fname']))
        if not serial.isdigit():
            new_serial = int(time.time())
            force_rebuild = True
            # it's a new serial
            self.log(
                'LOG_NOTICE', "{0} appears to be a new zone. Building {1} "
                "with initial serial {2}".format(soa, file_meta['prod_fname'],
                                                 new_serial),
                soa=soa)
        elif int(serial) != soa.serial:
            # Looks like someone made some changes... let's nuke them.
            # We should probably email someone too.
            self.log(
                'LOG_NOTICE', "{0} has serial {1} in svn ({2}) and serial "
                "{3} in the database. Zone will be rebuilt."
                .format(soa, serial, file_meta['prod_fname'],
                        soa.serial),
                soa=soa)
            force_rebuild = True
            # Choose the highest serial so any slave nameservers don't get
            # confused.
            new_serial = max(int(serial), soa.serial)

        return force_rebuild, new_serial

    def get_file_meta(self, view, root_domain, soa):
        file_meta = {}
        relative_zone_dir = self.calc_target(root_domain, soa)
        file_meta['fname'] = self.calc_fname(view, root_domain)
        file_meta['rel_fname'] = os.path.join(relative_zone_dir,
                                              file_meta['fname'])
        file_meta['prod_fname'] = os.path.join(self.PROD_DIR,
                                               file_meta['rel_fname'])
        return file_meta

    def build_zone_files(self):
        zone_stmts = {}

        for soa in SOA.objects.all():
            # General order of things:
            # * Find which views should have a zone file built and add them to
            #   a list.
            # * If any of the view's zone file have been tampered with or the
            #   zone is new, trigger the rebuilding of all the zone's view
            #   files. (rebuil all views in a zone keeps the serial
            #   synced across all views)
            # * Either rebuild all of a zone's view files because one view
            #   needed to be rebuilt due to tampering or the zone was dirty
            #   (again, this is to keep their serial synced) or just call
            #   named-checkzone on the existing zone files for good measure.
            #   Also generate a zone statement and add it to a dictionary for
            #   later use during BIND configuration generation.
            self.log('LOG_INFO', '====== Processing {0} {1} ======'.format(
                soa.root_domain, soa.serial)
            )
            views_to_build = []
            force_rebuild = soa.dirty
            self.log('LOG_INFO', "SOA was seen with dity == {0}".
                     format(force_rebuild), soa=soa)

            # By setting dirty to false now rather than later we get around the
            # edge case that someone updates a record mid build.
            soa.dirty = False
            soa.save()

            # This for loop decides which views will be canidates for
            # rebuilding.
            for view in View.objects.all():
                self.log('LOG_INFO', "++++++ Looking at < {0} > view ++++++".
                         format(view.name), soa=soa)
                t_start = time.time()  # tic
                view_data = build_zone_data(view, soa.root_domain, soa,
                                            logf=self.log)
                build_time = time.time() - t_start  # toc
                self.log('LOG_INFO', '< {0} > Built {1} data in {2} seconds'
                         .format(view.name, soa, build_time), soa=soa,
                         build_time=build_time)
                if not view_data:
                    self.log('LOG_INFO', '< {0} > No data found in this view. '
                             'No zone file will be made or included in any '
                             'config for this view.'.format(view.name),
                             soa=soa)
                    continue
                self.log('LOG_INFO', '< {0} > Non-empty data set for this '
                         'view. Its zone file will be included in the '
                         'config.'.format(view.name), soa=soa)
                file_meta = self.get_file_meta(view, soa.root_domain, soa)
                was_bad_prev, new_serial = self.verify_previous_build(
                    file_meta, view, soa.root_domain, soa
                )

                if was_bad_prev:
                    soa.serial = new_serial
                    force_rebuild = True

                views_to_build.append(
                    (view, file_meta, view_data)
                )

            self.log(
                'LOG_INFO', '----- Building < {0} > ------'.format(
                    ' | '.join([view.name for view, _, _ in views_to_build])
                ), soa=soa
            )

            if force_rebuild:
                # Bypass save so we don't have to save a possible stale 'dirty'
                # value to the db.
                SOA.objects.filter(pk=soa.pk).update(serial=soa.serial + 1)
                self.log('LOG_INFO', 'Zone will be rebuilt at serial {0}'
                         .format(soa.serial), soa=soa)
            else:
                self.log('LOG_INFO', 'Zone is stable at serial {0}'
                         .format(soa.serial), soa=soa)

            for view, file_meta, view_data in views_to_build:
                view_zone_stmts = zone_stmts.setdefault(view.name, [])
                # If we see a view in this loop it's going to end up in the
                # config
                view_zone_stmts.append(
                    self.render_zone_stmt(soa.root_domain,
                                          file_meta['prod_fname'])
                )
                # If it's dirty or we are rebuilding another view, rebuild the
                # zone
                if force_rebuild:
                    self.log('LOG_INFO', 'Rebuilding < {0} > view file '
                             '{1}'.format(view.name, file_meta['prod_fname']),
                             soa=soa)
                    prod_fname = self.build_zone(
                        view, file_meta,
                        # Lazy string evaluation
                        view_data.format(serial=soa.serial + 1),
                        soa.root_domain, soa
                    )
                    assert prod_fname == file_meta['prod_fname']
                else:
                    self.log(
                        'LOG_INFO',
                        'NO REBUILD needed for < {0} > view file {1}'.format(
                            view.name, file_meta['prod_fname']),
                        soa=soa
                    )
                # run named-checkzone for good measure
                    self.named_checkzone(
                        file_meta['prod_fname'], soa.root_domain, soa
                    )

        return zone_stmts

    def build_view_config(self, view_name, ztype, stmts):
        config_fname = "{0}.{1}".format(ztype, view_name)
        zone_stmts = '\n'.join(stmts).format(ztype=ztype)
        stage_config = self.write_stage_config(config_fname, zone_stmts)
        self.named_checkconf(stage_config)
        return self.stage_to_prod(stage_config)

    def build_config_files(self, zone_stmts):
        # named-checkconf on config files
        self.log('LOG_INFO', self.format_title("Building config files"))
        configs = []
        self.log(
            'LOG_INFO', "Building configs for views < {0} >".format(
                ' | '.join([view_name for view_name in zone_stmts.keys()])
            )
        )
        for view_name, view_stmts in zone_stmts.iteritems():
            self.log('LOG_INFO', "Building config for view < {0} >".
                     format(view_name))
            configs.append(
                self.build_view_config(view_name, 'master', view_stmts)
            )
        return configs

    def check_stop_update(self):
        """
        Look for a file referenced by `STOP_UPDATE_FILE` and if it exists,
        cancel the build.
        """
        if os.path.exists(self.STOP_UPDATE_FILE):
            msg = "The STOP_UPDATE_FILE ({0}) exists. Build canceled".format(
                self.STOP_UPDATE_FILE)
            self.log('LOG_INFO', msg)
            raise BuildError(msg)

    def build_dns(self):
        self.check_stop_update()
        self.log('LOG_NOTICE', 'Building...')
        self.lock()
        try:
            if self.CLOBBER_STAGE:
                self.clear_staging(force=True)
            self.build_staging()

            # zone files
            if self.BUILD_ZONES:
                self.build_config_files(self.build_zone_files())
            else:
                self.log('LOG_INFO', "BUILD_ZONES is False. Not "
                         "building zone files.")

            self.log('LOG_INFO', self.format_title("VCS Checkin"))
            if self.BUILD_ZONES and self.PUSH_TO_PROD:
                self.vcs_checkin()
            else:
                self.log('LOG_INFO', "PUSH_TO_PROD is False. Not checking "
                         "into {0}".format(self.vcs_type))

            self.log('LOG_INFO', self.format_title("Handle Staging"))
            if self.PRESERVE_STAGE:
                self.log('LOG_INFO', "PRESERVE_STAGE is True. Not "
                         "removing staging. You will need to use "
                         "--clobber-stage on the next run.")
            else:
                self.clear_staging()
        # All errors are handled by caller (this function)
        except BuildError:
            self.log('LOG_NOTICE', 'Error during build. Not removing staging')
            raise
        except Exception:
            self.log('LOG_NOTICE', 'Error during build. Not removing staging')
            raise
        finally:
            # Clean up
            self.log('LOG_INFO', self.format_title("Release Mutex"))
            self.unlock()
        self.log('LOG_NOTICE', 'Successful build is successful.')
