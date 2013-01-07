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


from logging import getLogger

from datetime import timedelta
from datetime import datetime
from dateutil.tz import tzutc

from splice.common import identity

from splice.common.models import RHICLookupTask

_LOG = getLogger(__name__)

def get_cached_status_code(uuid):
    """
    @param uuid: RHIC uuid
    @return:
    """
    t = identity.get_current_rhic_lookup_tasks(uuid)
    if t and t.completed:
        return t.status_code
    return None

def create_rhic_lookup_task(uuid):
    """
    @param uuid: RHIC uuid
    @return:
    """
    _LOG.info("create_rhic_lookup_task(%s)" % (uuid))
    # To avoid circular import
    # where we import 'identity_lookup' from splice.entitlement.tasks
    from splice.entitlement import tasks
    result = tasks.sync_single_rhic.apply_async((uuid,))
    task = update_rhic_lookup_task(uuid, result.task_id)
    _LOG.info("create_rhic_lookup_task(%s) created lookup task: '%s'" % (uuid, task))
    return task

def complete_rhic_lookup_task(uuid, status_code):
    """
    @param uuid: RHIC uuid
    @param status_code: HTTP status code from RHIC lookup
    @return: None
    """
    _LOG.info("complete_rhic_lookup_task(rhic_uuid='%s', status_code='%s') invoked" % (uuid, status_code))
    current_task = identity.get_current_rhic_lookup_tasks(uuid)
    if not current_task:
        _LOG.warning("completed_rhic_lookup_task with status code '%s' called on uuid '%s' "
                     "yet no task was found" % (status_code, uuid))
        return None
    if status_code in [202, 404]:
        #   202 - in-progress tasks
        #   404 - lookups that received a definitive response of the RHIC not existing.
        current_task.task_id = None
        current_task.modified = datetime.now(tzutc())
        current_task.status_code = status_code
        current_task.completed = True
        if status_code == 202:
            # Parent is still processing request, task will remain active.
            current_task.completed = False
        current_task.save()
    else:
        # Task will be killed, it either succeeded with a '200' or an unexpected error was seen.
        msg = "Received [%s] for lookup of RHIC [%s]" % (status_code, uuid)
        if status_code in [200]:
            # 200 - RHIC was found in parent
            _LOG.info(msg)
        else:
            _LOG.error(msg)
        identity.delete_rhic_lookup(current_task)
    return None


def update_rhic_lookup_task(uuid, task_id):
    _LOG.info("update_rhic_lookup_task(rhic_uuid='%s', task_id='%s')" % (uuid, task_id))
    current_task = identity.get_current_rhic_lookup_tasks(uuid)
    if not current_task:
        current_task = RHICLookupTask(uuid=uuid, initiated=datetime.now(tzutc()))
    current_task.task_id = task_id
    current_task.modified = datetime.now(tzutc())
    current_task.completed = False
    current_task.save()
    _LOG.info("update_rhic_lookup_task(%s, %s) updated task to %s" % (uuid, task_id, current_task))
    return current_task
