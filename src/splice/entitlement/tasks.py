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


# Placeholder for celery tasks
from celery import Celery
from datetime import datetime
from logging import getLogger

from splice.common.constants import SPLICE_ENTITLEMENT_BASE_TASK_NAME
from splice.common.identity import sync_from_rhic_serve_blocking
from splice.common import celeryconfig

_LOG = getLogger(__name__)

celery = Celery(SPLICE_ENTITLEMENT_BASE_TASK_NAME)
celery.config_from_object(celeryconfig)

@celery.task(name="%s.add" % (SPLICE_ENTITLEMENT_BASE_TASK_NAME))
def add(x, y):
    return x + y

@celery.task(name="%s.mul" % SPLICE_ENTITLEMENT_BASE_TASK_NAME)
def mul(x, y):
    return x * y

@celery.task(name="%s.xsum" % SPLICE_ENTITLEMENT_BASE_TASK_NAME)
def xsum(numbers):
    return sum(numbers)

@celery.task(name="%s.sync_rhics" % SPLICE_ENTITLEMENT_BASE_TASK_NAME)
def sync_rhics():
    """
    Will synchronize RHIC to product mapping data from a RCS server.
    @return: status of synchronization, with optional error message:
             (True, "") - on success
             (False, "error message here") - on failure
    @rtype:  (bool,str)
    """
    _LOG.info("Celery task: sync_rhics invoked")
    retval = sync_from_rhic_serve_blocking()
    _LOG.info("Celery task: sync_rhics finished")
    return retval

@celery.task(name="%s.log_time" % SPLICE_ENTITLEMENT_BASE_TASK_NAME)
def log_time():
    _LOG.info("Celery task: log_time invoked.  Current time is: %s" % datetime.now())
