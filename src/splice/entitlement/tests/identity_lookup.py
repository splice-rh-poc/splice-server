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

import logging
import pytz

from splice.common.models import RHICLookupTask
from splice.managers import identity_lookup

# Unit test imports
from base import BaseEntitlementTestCase

LOG = logging.getLogger(__name__)


class IdentityLookupTest(BaseEntitlementTestCase):
    def setUp(self):
        super(IdentityLookupTest, self).setUp()

    def tearDown(self):
        super(IdentityLookupTest, self).tearDown()

    def test_update_rhic_lookup_task(self):
        task_a = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a11111111111", completed=False, task_id=None)
        task_a.save()
        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(task_a.uuid, found[0].uuid)
        self.assertIsNone(found[0].task_id)
        prior_modified = task_a.modified

        # Ensure that 'modified' has been updated to new time
        # and the 'task_id' has been noted
        task_id = "1"
        ret_val = identity_lookup.update_rhic_lookup_task(task_a.uuid, task_id)
        self.assertEquals(ret_val.uuid, task_a.uuid)
        self.assertFalse(ret_val.completed)
        self.assertEquals(ret_val.task_id, task_id)
        self.assertTrue(ret_val.modified > prior_modified)

        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, task_a.uuid)
        self.assertFalse(found[0].completed)
        self.assertEquals(found[0].task_id, task_id)
        self.assertTrue(found[0].modified > prior_modified)


    def test_complete_rhic_lookup_task_200(self):
        task = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a11111111111", completed=False, task_id=None)
        task.save()
        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, task.uuid)

        # Mark as '200', a successful complete which will remove the task from the lookup db
        accepted = 200
        ret_val = identity_lookup.complete_rhic_lookup_task(task.uuid, accepted)
        self.assertIsNone(ret_val)
        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 0)

    def test_complete_rhic_lookup_task_404(self):
        task = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a11111111111", completed=False, task_id=None)
        task.save()
        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, task.uuid)

        # Mark as '404', task finished and received answer RHIC is unknown
        # task should be cached in DB with '404' status_code
        # it should be marked as 'completed=True'
        not_found = 404
        ret_val = identity_lookup.complete_rhic_lookup_task(task.uuid, not_found)
        self.assertIsNotNone(ret_val)
        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, task.uuid)
        self.assertIsNone(found[0].task_id)
        self.assertEquals(found[0].status_code, not_found)
        self.assertTrue(found[0].completed)

    def test_complete_rhic_lookup_task_202(self):
        task = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a11111111111", completed=False, task_id=None)
        task.save()
        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, task.uuid)

        # Mark as '202', meaning we haven't found an answer yet, let the tasks continue
        # task should remain in DB, should be marked as 'completed=False'
        in_progress = 202
        ret_val = identity_lookup.complete_rhic_lookup_task(task.uuid, in_progress)
        self.assertIsNotNone(ret_val)
        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, task.uuid)
        self.assertIsNone(found[0].task_id)
        self.assertEquals(found[0].status_code, in_progress)
        self.assertFalse(found[0].completed)


    def test_complete_rhic_lookup_task_unexpected_value(self):
        task = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a11111111111", completed=False, task_id=None)
        task.save()
        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, task.uuid)

        # Mark task with an odd unexpected value, we will mark the task as completed=True
        # and store the status_code
        unexpected = 123
        ret_val = identity_lookup.complete_rhic_lookup_task(task.uuid, unexpected)
        self.assertIsNotNone(ret_val)
        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, task.uuid)
        self.assertIsNone(found[0].task_id)
        self.assertEquals(found[0].status_code, unexpected)
        self.assertTrue(found[0].completed)
