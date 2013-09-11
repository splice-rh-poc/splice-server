# -*- coding: utf-8 -*-
#
# Copyright © 2013 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

import logging
import logging.handlers

import os

#Bug 1006593 - splice log rolling sets incorrect permissions 
#https://bugzilla.redhat.com/show_bug.cgi?id=1006593
# Below will fix an issue when a logging file rotates over a new file is created
# we want the new logging file to be group writeable, by default it's only group readable.
#
# The Splice mod_wsgi webapp and spacewalk-splice-checkin share the same logging files
# we want to ensure that both apps are able to write to the files
# spacewalk-splice-checkin runs as 'splice' user
# mod_wsgi app runs as 'apache' user
# both apps run as group 'splice'
# We need the logging files to always be owned by 'splice'
#
# Following example from:
# http://stackoverflow.com/questions/1407474/does-python-logging-handlers-rotatingfilehandler-allow-creation-of-a-group-writa
class GroupWriteRotatingFileHandler(logging.handlers.RotatingFileHandler):
    def _open(self):
        prevumask = os.umask(0002)
        rtv=logging.handlers.RotatingFileHandler._open(self)
        os.umask(prevumask)
        return rtv

logging.handlers.GroupWriteRotatingFileHandler = GroupWriteRotatingFileHandler
