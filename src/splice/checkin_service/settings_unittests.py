# -*- coding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


# Django settings for checkin_service project.
import logging
import logging.config
import os
import pwd

from splice.common import config
from splice.dev.settings import *

# Initialize Splice Config
DEBUG_LOG_CONFIG_FILE = "src/splice/test_data/log_unittests.cfg"
# Logging config file requires /tmp/splice exists
if not os.path.exists("/tmp/splice"):
    os.makedirs("/tmp/splice")

splice_log_cfg = DEBUG_LOG_CONFIG_FILE
if splice_log_cfg:
    if not os.path.exists(splice_log_cfg):
        print "Unable to read '%s' for logging configuration" % (splice_log_cfg)
    else:
        config.reset_logging()
        logging.config.fileConfig(splice_log_cfg)

from logging import getLogger
_LOG = getLogger(__name__)

##
## Adding mongoengine specifics ##
##
MONGO_DATABASE_NAME = 'TEST_checkin_service'
import mongoengine
mongoengine.connect(MONGO_DATABASE_NAME)
mongoengine.register_connection("rhic_serve", MONGO_DATABASE_NAME)
##
## End mongoengine specifics
##
