#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2010 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.



# This script is intended to be run from a git checkout of RCS
#  it will create symlinks and update paths as needed so RCS can be
#  run without needing to install the RPM.
# Script is based on 'pulp-dev.py' from pulpproject.org

import optparse
import os
import shlex
import shutil
import sys
import subprocess

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DJANGO_APP_DIR = os.path.join(BASE_DIR, "src", "splice")

WARNING_COLOR = '\033[31m'
WARNING_RESET = '\033[0m'

DIRS = ("/etc/splice",
        "/etc/pki/splice",
        "/var/log/splice",
        "/srv/splice",
        )

LINKS = (
            ('etc/httpd/conf.d/splice.conf', '/etc/httpd/conf.d/splice.conf'),
            ('etc/pki/splice/Splice_testing_root_CA.crt', '/etc/pki/splice/Splice_testing_root_CA.crt'),
            ('etc/pki/splice/Splice_testing_root_CA.key', '/etc/pki/splice/Splice_testing_root_CA.key'),
            ('etc/rc.d/init.d/splice_celerybeat', '/etc/rc.d/init.d/splice_celerybeat'),
            ('etc/rc.d/init.d/splice_celeryd', '/etc/rc.d/init.d/splice_celeryd'),
            ('etc/splice/celery', '/etc/splice/celery'),
            ('etc/splice/server.conf', '/etc/splice/server.conf'),
            ('srv/splice/webservices.wsgi', '/srv/splice/webservices.wsgi'),
        )

def parse_cmdline():
    """
    Parse and validate the command line options.
    """
    parser = optparse.OptionParser()
    parser.add_option('-I', '--install', action='store_true', help='install pulp development files')
    parser.add_option('-U', '--uninstall', action='store_true', help='uninstall pulp development files')
    parser.set_defaults(install=False, uninstall=False)
    opts, args = parser.parse_args()
    if opts.install and opts.uninstall:
        parser.error('both install and uninstall specified')
    if not (opts.install or opts.uninstall):
        parser.error('neither install or uninstall specified')
    return (opts, args)

def warning(msg):
    print "%s%s%s" % (WARNING_COLOR, msg, WARNING_RESET)

def debug(opts, msg):
    sys.stderr.write('%s\n' % msg)

def create_dirs(opts):
    for d in DIRS:
        if os.path.exists(d) and os.path.isdir(d):
            debug(opts, 'skipping %s exists' % d)
            continue
        debug(opts, 'creating directory: %s' % d)
        os.makedirs(d, 0777)

def getlinks():
    links = []
    for l in LINKS:
        if isinstance(l, (list, tuple)):
            src = l[0]
            dst = l[1]
        else:
            src = l
            dst = os.path.join('/', l)
        links.append((src, dst))
    return links

def install(opts):
    warnings = []
    create_dirs(opts)
    currdir = os.path.abspath(os.path.dirname(__file__))
    for src, dst in getlinks():
        warning_msg = create_link(opts, os.path.join(currdir,src), dst)
        if warning_msg:
            warnings.append(warning_msg)
    if warnings:
        print "\n***\nPossible problems:  Please read below\n***"
        for w in warnings:
            warning(w)
    update_celeryd_config()
    update_permissions()
    return os.EX_OK

def uninstall(opts):
    for src, dst in getlinks():
        debug(opts, 'removing link: %s' % dst)
        if not os.path.islink(dst):
            debug(opts, '%s does not exist, skipping' % dst)
            continue
        os.unlink(dst)
    return os.EX_OK


def create_link(opts, src, dst):
    if not os.path.lexists(dst):
        return _create_link(opts, src, dst)

    if not os.path.islink(dst):
        return "[%s] is not a symbolic link as we expected, please adjust if this is not what you intended." % (dst)

    if not os.path.exists(os.readlink(dst)):
        warning('BROKEN LINK: [%s] attempting to delete and fix it to point to %s.' % (dst, src))
        try:
            os.unlink(dst)
            return _create_link(opts, src, dst)
        except:
            msg = "[%s] was a broken symlink, failed to delete and relink to [%s], please fix this manually" % (dst, src)
            return msg

    debug(opts, 'verifying link: %s points to %s' % (dst, src))
    dst_stat = os.stat(dst)
    src_stat = os.stat(src)
    if dst_stat.st_ino != src_stat.st_ino:
        msg = "[%s] is pointing to [%s] which is different than the intended target [%s]" % (dst, os.readlink(dst), src)
        return msg

def _create_link(opts, src, dst):
        debug(opts, 'creating link: %s pointing to %s' % (dst, src))
        try:
            os.symlink(src, dst)
        except OSError, e:
            msg = "Unable to create symlink for [%s] pointing to [%s], received error: <%s>" % (dst, src, e)
            return msg

def update_celeryd_config():
    # Update celeryd configuration
    django_dir = DJANGO_APP_DIR.replace("/", "\/")
    cmd = "sed -i 's/^CELERYD_CHDIR=.*/CELERYD_CHDIR=%s/' %s" % (django_dir, '/etc/splice/celery/celeryd')
    run_command(cmd)

def update_permissions():
    cmd = "chown -R apache:apache /var/log/splice"
    run_command(cmd)
    cmd = "chmod 3775 /var/log/splice"
    run_command(cmd)

def run_command(cmd, verbose=True):
    if verbose:
        print "Running: %s" % (cmd)
    if isinstance(cmd, str):
        cmd = shlex.split(cmd.encode('ascii', 'ignore'))
    handle = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out_msg, err_msg = handle.communicate(None)
    if handle.returncode != 0:
        print "Error running: %s" % (cmd)
        print "stdout:\n%s" % (out_msg)
        print "stderr:\n%s" % (err_msg)
        return False
    return True, out_msg, err_msg


if __name__ == '__main__':
    opts, args = parse_cmdline()
    if opts.install:
        sys.exit(install(opts))
    if opts.uninstall:
        sys.exit(uninstall(opts))

