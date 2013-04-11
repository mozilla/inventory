"""
Deploy this project in dev/stage/production.

Requires commander_ which is installed on the systems that need it.

.. _commander: https://github.com/oremj/commander
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from commander.deploy import task, hostgroups
import commander_settings as settings


@task
def update_code(ctx, tag):
    """Update the code to a specific git reference (tag/sha/etc)."""
    with ctx.lcd(settings.SRC_DIR):
        ctx.local('git fetch')
        ctx.local('git checkout -f %s' % tag)
        ctx.local('git submodule sync')
        ctx.local('git submodule update --init --recursive')


@task
def update_info(ctx):
    """Write info about the current state to a publicly visible file."""
    with ctx.lcd(settings.SRC_DIR):
        ctx.local('date')
        ctx.local('git branch -a')
        ctx.local('git log -3')
        ctx.local('git status')
        ctx.local('git submodule status')
        ctx.local('git rev-parse HEAD > media/revision.txt')

@task
def update_db(ctx):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local('python2.6 manage.py migrate')
        ctx.local('python2.6 manage.py migrate --list')

@task
def clean(ctx):
    """Clean .gitignore and .pyc files."""
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("find . -type f -name '.gitignore' -or -name '*.pyc' -delete")


@task
def checkin_changes(ctx):
    """Use the local, IT-written deploy script to check in changes."""
    ctx.local(settings.DEPLOY_SCRIPT)


@hostgroups(settings.WEB_HOSTGROUP, remote_kwargs={'ssh_key': settings.SSH_KEY})
def deploy_app(ctx):
    """Call the remote update script to push changes to webheads."""
    ctx.remote('touch %s' % settings.REMOTE_WSGI)


# https://github.com/mozilla/chief/blob/master/chief.py#L48


@task
def pre_update(ctx, ref=settings.UPDATE_REF):
    """1. Update code to pick up changes to this file."""
    update_code(ref)
    update_info()
    clean()


@task
def update(ctx):
    """2. Nothing to do here yet."""
    update_db()


@task
def deploy(ctx):
    """3. Deploy stuff."""
    checkin_changes()
    deploy_app()
