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
import os

from datetime import datetime, timedelta
from dateutil.tz import tzutc
from logging import getLogger
from mongoengine.queryset import NotUniqueError

from splice.common.models import SingleTaskInfo

_LOG = getLogger(__name__)

###
# This class will use 2 ways of accessing MongoDB
# 1) mongoengine - used primarily to save 'SingleTaskInfo' objects to Mongo
# 2) pymongo     - used to invoke an atomic operation 'find_and_modify' which mongoengine does not expose
#
# We form the connection through pymongo by asking mongoengine's SingleTaskInfo for the pymongo collection it is using
# next we defer the lookup of this pymongo collection until we are servicing the method, this helps to ensure we use
# the same connection to pymongo.  This is needed if some init code changes the DB info after loading classes, like
# what we see when running unit tests
###
class EnforceSingleTask:

    @classmethod
    def _get_collection(cls):
        # We are defering when this gets called because we saw issues with resolving to the unit test database
        # when this was simply added as class level variable.
        # We need this to be invoked after the unit tests have switched over to their own database
        # Otherwise we run the risk of using 2 DBs:
        # - one for general mongoengine calls for SingleTaskInfo.save()
        # - second for pymongo find_and_modify()
        return SingleTaskInfo._get_collection()

    @classmethod
    def check_pid(cls, pid):
        """
        Check's if a Unix process is alive with PID of 'pid'
        @param pid: Unix process' pid to check
        @return: True if alive, False otherwise
        """
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True

    @classmethod
    def remove_not_running(cls, task_id):
        existing_task = SingleTaskInfo.objects(task_id=task_id).first()
        if existing_task:
            if not cls.check_pid(existing_task.owner_pid):
                # Rationale for why this is safe from race conditions.
                #  'remove_by_owner' will only delete the task if the entry is still 'owned' by the dead PID
                #  if another process cleans this up then the entry will be owned by a different PID and
                #  the findAndModify will not find the entry and results in no change.
                ret_val = cls.remove_by_owner(task_id, existing_task.owner_pid)
                if not ret_val:
                    _LOG.warning("Unsuccessful in removing a task info entry on '%s' from pid '%s' created on '%s'." % \
                                 (task_id, existing_task.owner_pid, existing_task.created))
                return ret_val

    @classmethod
    def remove_expired(cls, task_id, seconds_expire):
        """
        @param task_id: a string identifer of the task
        @param seconds_expire: an integer representing when we would consider this task expired if a lock is in DB
        @return: object if it was deleted, None if nothing was deleted
        """
        expired_time = datetime.now(tzutc()) - timedelta(seconds=seconds_expire)
        #  Using an atomic operation of findAndModify to delete entry if it exists and is expired
        return cls._get_collection().find_and_modify(query={"task_id":task_id, "created": {"$lte": expired_time}}, remove=True)

    @classmethod
    def remove_by_owner(cls, task_id, owner_pid):
        """
        Will remove a lock for the task specified by 'task_id', only if the lock entry was created by 'owner_pid'
        @task_id: a string identifier of the task
        @owner_pid: an integer representing the pid of the caller
        @return: object if it was deleted, None if nothing was deleted
        """
        #  Using an atomic operation of findAndModify to delete entry if it exists and still 'owned' by this PID
        return cls._get_collection().find_and_modify(query={"task_id":task_id, "owner_pid": int(owner_pid)}, remove=True)

    @classmethod
    def lock(cls, task_id, seconds_expire):
        # Rationale:
        #  It is possible that this task may run and clean an expired task yet not be able to 'obtain a lock',
        #  as another process may be able to write the entry first.  This is fine.  Our concern is simply to allow
        #  only 1 to form the lock.
        cls.remove_not_running(task_id)
        cls.remove_expired(task_id, seconds_expire)
        obj = SingleTaskInfo(task_id=task_id, owner_pid=os.getpid())
        try:
            obj.save()
        except  NotUniqueError, e:
            return False
        else:
            return True

    @classmethod
    def release(cls, task_id):
        return cls.remove_by_owner(task_id, owner_pid=os.getpid())

##
# Decorator to be used by celery tasks to enforce only one of that specific task may run at a time
# Will enforce this through mulitple processes by using a MongoDB backed and atomic 'findAndModify'
def single_instance_task(seconds_expire=30*60, name=None):
    """
    Decorator that will ensure only 1 instance of a task is able to execute

    @param seconds_expire: controls when we determine an existing task entry is expired and can be deleted
    @param task_id: optional way to override what 'task_id' to use.  Generally leave this as 'None' and we
                    will chose an id based on the function being decorated
    @return:
    """
    def task_exc(func):
        def wrapper(*args, **kwargs):
            if name:
                task_id = name
            else:
                task_id = "single_instance_task-%s" % (func.__name__)
            if EnforceSingleTask.lock(task_id, seconds_expire):
                try:
                    func(*args, **kwargs)
                finally:
                    EnforceSingleTask.release(task_id)
            else:
                _LOG.info("Skipping run of task '%s' since not able to obtain a lock for '%s'" % (func.__name__), task_id)
        return wrapper
    return task_exc
