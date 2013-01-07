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

import time

from celery import Celery
from celery.result import AsyncResult
from datetime import timedelta
from datetime import datetime
from dateutil.tz import tzutc
from logging import getLogger

from splice.common.constants import SPLICE_ENTITLEMENT_BASE_TASK_NAME
from splice.common import identity
from splice.common import celeryconfig
from splice.managers import identity_lookup, upload

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

@celery.task(name="%s.sync_single_rhic" % SPLICE_ENTITLEMENT_BASE_TASK_NAME)
def sync_single_rhic(uuid):
    """
    Will sync data on a single RHIC specified by the 'uuid'
    @param uuid: uuid of a rhic to sync from our parent
    @type uuid: str
    @return:
    """
    start = time.time()
    _LOG.info("Sync RHIC uuid=%s" % (uuid))
    status_code  = identity.sync_single_rhic_blocking(uuid)
    identity_lookup.complete_rhic_lookup_task(uuid, status_code)
    end = time.time()
    _LOG.info("Sync RHIC uuid=%s task completed with status_code '%s' in %s seconds" % \
              (uuid, status_code, end-start))
    return status_code

@celery.task(name="%s.sync_all_rhics" % SPLICE_ENTITLEMENT_BASE_TASK_NAME)
def sync_rhics():
    """
    Will synchronize RHIC to product mapping data from a RCS server.
    @return: status of synchronization, with optional error message:
             (True, "") - on success
             (False, "error message here") - on failure
    @rtype:  (bool,str)
    """
    start = time.time()
    _LOG.info("invoked")
    retval = identity.sync_from_rhic_serve_blocking()
    end = time.time()
    _LOG.info("finished in %s seconds" % (end-start))
    return retval

@celery.task(name="%s.process_running_rhic_lookup_tasks" % SPLICE_ENTITLEMENT_BASE_TASK_NAME)
def process_running_rhic_lookup_tasks():
    start = time.time()
    _LOG.info("invoked")
    identity.purge_expired_rhic_lookups()
    in_progress_tasks = identity.get_in_progress_rhic_lookups()
    _LOG.info("%s in progress tasks exist" % (len(in_progress_tasks)))
    for t in in_progress_tasks:
        if t.task_id:
            result = AsyncResult(t.task_id)
            if result.state in ["RUNNING", "PENDING"]:
                _LOG.info("skipped '%s' since it is %s" % (t, result.state))
                continue
            else:
                _LOG.info("found existing "
                          "celery task with id '%s' and state '%s'.  Will issue a new task "
                          "since state was not RUNNING or PENDING." % (t.task_id, result.state))
        new_result = sync_single_rhic.apply_async((t.uuid,))
        new_task = identity_lookup.update_rhic_lookup_task(t.uuid, new_result.task_id)
        _LOG.info("initiated new task: %s" % (new_task))
    end = time.time()
    _LOG.info("completed in %s seconds" % (end-start))

@celery.task(name="%s.log_time" % SPLICE_ENTITLEMENT_BASE_TASK_NAME)
def log_time():
    _LOG.info("Celery task: log_time invoked.  Current time is: %s" % datetime.now())

@celery.task(name="%s.upload_product_usage" % SPLICE_ENTITLEMENT_BASE_TASK_NAME)
def upload_product_usage():
    _LOG.info("invoked")
    upload.upload_product_usage_data()
    _LOG.info("completed")

