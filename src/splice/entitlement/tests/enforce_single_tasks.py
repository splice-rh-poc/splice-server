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

from datetime import datetime, timedelta
from dateutil.tz import tzutc
import logging
import os

from splice.common.enforce_single_tasks import EnforceSingleTask, single_instance_task
from splice.common.models import SingleTaskInfo

# Unit test imports
from base import BaseEntitlementTestCase

LOG = logging.getLogger(__name__)

class EnforceSingleTasksTest(BaseEntitlementTestCase):
    def setUp(self):
        super(EnforceSingleTasksTest, self).setUp()

    def tearDown(self):
        super(EnforceSingleTasksTest, self).tearDown()

    def test_check_pid(self):
        self.assertTrue(EnforceSingleTask.check_pid(os.getpid()))
        # Unsure how to determine a PID which definitely isn't running
        # instead will look at a range and first time we receive a false will
        # assume this is working correctly and PID wasn't running
        found = False
        for pid in range(1000, 20000):
             if not EnforceSingleTask.check_pid(pid):
                found = True
                break
        self.assertTrue(found)

    def test_remove_not_running(self):
        not_running = None
        for pid in range(1000, 20000):
             if not EnforceSingleTask.check_pid(pid):
                not_running = pid
                break
        self.assertIsNotNone(not_running)
        ##
        # Create an entry 'owned' by PID of 'not_running'
        ##
        task_id = "test_remove_not_running_task_id"
        entry = SingleTaskInfo(task_id=task_id, owner_pid=not_running)
        entry.save()
        self.assertEquals(1, SingleTaskInfo.objects(task_id=task_id).count())
        retval = EnforceSingleTask.remove_not_running(task_id)
        self.assertIsNotNone(retval)
        # verify it has been removed
        self.assertEquals(0, SingleTaskInfo.objects(task_id=task_id).count())
        ##
        # Create an entry 'owned' by running PID, verify it is not removed
        ##
        entry = SingleTaskInfo(task_id=task_id, owner_pid=os.getpid())
        entry.save()
        self.assertEquals(1, SingleTaskInfo.objects(task_id=task_id).count())
        retval = EnforceSingleTask.remove_not_running(task_id)
        # verify it has _not_ been removed
        self.assertIsNone(retval)
        self.assertEquals(1, SingleTaskInfo.objects(task_id=task_id).count())

    def test_remove_expired(self):
        # Create an 'expired' entry
        threshold=5
        task_id = "test_remove_expored_task_id"
        created = datetime.now(tzutc()) - timedelta(seconds=threshold+1)
        entry = SingleTaskInfo(task_id=task_id, owner_pid=os.getpid(), created=created)
        entry.save()
        self.assertEquals(1, SingleTaskInfo.objects(task_id=task_id).count())
        retval = EnforceSingleTask.remove_expired(task_id, seconds_expire=threshold)
        # Verify it is removed
        self.assertIsNotNone(retval)
        self.assertEquals(0, SingleTaskInfo.objects(task_id=task_id).count())
        ##
        # Create an entry that is not expired
        ##
        created = datetime.now(tzutc())
        entry = SingleTaskInfo(task_id=task_id, owner_pid=os.getpid(), created=created)
        entry.save()
        self.assertEquals(1, SingleTaskInfo.objects(task_id=task_id).count())
        retval = EnforceSingleTask.remove_expired(task_id, seconds_expire=threshold)
        # Verify it is _not_ removed
        self.assertIsNone(retval)
        self.assertEquals(1, SingleTaskInfo.objects(task_id=task_id).count())

    def test_remove_by_owner(self):
        task_id = "test_remove_by_owner_task_id"
        pid = os.getpid()
        entry = SingleTaskInfo(task_id=task_id, owner_pid=pid)
        entry.save()
        self.assertEquals(1, SingleTaskInfo.objects(task_id=task_id).count())
        retval = EnforceSingleTask.remove_by_owner(task_id, pid)
        self.assertIsNotNone(retval)
        self.assertEquals(0, SingleTaskInfo.objects(task_id=task_id).count())
        ##
        # Simulate how another process that used there own pid wouldn't
        # delete the entry
        ##
        pid = os.getpid() + 1
        entry = SingleTaskInfo(task_id=task_id, owner_pid=pid)
        entry.save()
        self.assertEquals(1, SingleTaskInfo.objects(task_id=task_id).count())
        retval = EnforceSingleTask.remove_by_owner(task_id, os.getpid())
        self.assertIsNone(retval)
        self.assertEquals(1, SingleTaskInfo.objects(task_id=task_id).count())

    def test_lock(self):
        task_id = "test_lock_task_id"
        threshold = 30
        retval = EnforceSingleTask.lock(task_id, seconds_expire=threshold)
        self.assertTrue(retval)
        # Subsequent call should fail since it has been 'locked'
        self.assertFalse(EnforceSingleTask.lock(task_id, seconds_expire=threshold))

    def test_release(self):
        task_id = "test_release_task_id"
        threshold = 30
        retval = EnforceSingleTask.lock(task_id, seconds_expire=threshold)
        self.assertTrue(retval)
        # Subsequent call should fail since it has been 'locked'
        self.assertFalse(EnforceSingleTask.lock(task_id, seconds_expire=threshold))
        self.assertIsNotNone(EnforceSingleTask.release(task_id))
        self.assertTrue(EnforceSingleTask.lock(task_id, seconds_expire=threshold))

    def test_release_from_diff_pid(self):
        # Create an entry from a dummy pid
        task_id = "test_release_from_diff_pid_task_id"
        pid = os.getpid() + 1
        entry = SingleTaskInfo(task_id=task_id, owner_pid=pid)
        entry.save()
        self.assertEquals(1, SingleTaskInfo.objects(task_id=task_id).count())
        self.assertIsNone(EnforceSingleTask.release(task_id))
        # Verify the remove did nothing because our 'pid' didn't match the entrie's pid
        self.assertEquals(1, SingleTaskInfo.objects(task_id=task_id).count())
