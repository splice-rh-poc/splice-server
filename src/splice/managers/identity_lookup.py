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

from splice.entitlement.models import RHICLookupTask

_LOG = getLogger(__name__)

def create_rhic_lookup_task(uuid):
    # To avoid circular import
    # where we import 'identity_lookup' from splice.entitlement.tasks
    from splice.entitlement import tasks
    result = tasks.sync_single_rhic.apply_async((uuid,))
    task = update_rhic_lookup_task(uuid, result.task_id)
    return task

def complete_rhic_lookup_task(uuid, status_code):
    current_task = identity.get_current_rhic_lookup_tasks(uuid)
    if not current_task:
        _LOG.warning("completed_rhic_lookup_task with status code '%s' called on uuid '%s' "
                     "yet no task was found" % (status_code, uuid))
        return None
    current_task.task_id = None
    current_task.modified = datetime.now(tzutc())
    current_task.status_code = status_code
    current_task.completed = True
    if status_code == 200:
        identity.delete_rhic_lookup(current_task)
        return None
    elif status_code == 202:
        # 202 is considered to be in_progress, so don't mark it as complete
        current_task.completed = False
    current_task.save()
    return current_task

def update_rhic_lookup_task(uuid, task_id):
    current_task = identity.get_current_rhic_lookup_tasks(uuid)
    if not current_task:
        current_task = RHICLookupTask(uuid=uuid)
    current_task.task_id = task_id
    current_task.modified = datetime.now(tzutc())
    current_task.completed = False
    current_task.save()
    return current_task