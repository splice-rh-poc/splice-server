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
import time
from threading import Thread, Lock
from uuid import UUID

from datetime import timedelta
from datetime import datetime
from dateutil.tz import tzutc
import pytz

from splice.common import config
from splice.common import rhic_serve_client
from splice.common.utils import convert_to_datetime, sanitize_key_for_mongo
from splice.entitlement.models import ConsumerIdentity, IdentitySyncInfo, RHICLookupTask

_LOG = logging.getLogger(__name__)

JOBS = {}
JOB_LOCK = Lock()

def is_rhic_lookup_task_expired(current_task):
    cfg = config.get_rhic_serve_config_info()
    if not current_task.completed:
        # Task is in progress, ensure that it's initiated time is within timeout range
        timeout_in_minutes = cfg["single_rhic_lookup_timeout_in_minutes"]
        threshold = current_task.initiated + timedelta(minutes=timeout_in_minutes)
        if not threshold.tzinfo:
            threshold = pytz.UTC.localize(threshold)
        if threshold < datetime.now(tzutc()):
            _LOG.info("Task has timed out, threshold was: %s.  Task = <%s>" % (threshold, current_task))
            # Current time is greater than the threshold this task had to stay alive
            # It is expired
            return True
    else:
        # Task has completed, check if it's within cached time boundaries
        valid_hours = cfg["single_rhic_lookup_cache_unknown_in_hours"]
        modified = current_task.modified
        if not modified.tzinfo:
            modified = pytz.UTC.localize(modified)
        threshold = datetime.now(tzutc()) - timedelta(hours=valid_hours)
        if modified < threshold:
            _LOG.info("Cached task has expired, threshold was: %s. Task = <%s>" % (threshold, current_task))
            # Task was modified more than # hours ago
            # It is expired
            return True
    return False

def purge_expired_rhic_lookups():
    all_tasks = RHICLookupTask.objects()
    for current_task in all_tasks:
        if is_rhic_lookup_task_expired(current_task):
            delete_rhic_lookup(current_task)

def get_in_progress_rhic_lookups():
    all_tasks = RHICLookupTask.objects(completed=False)
    ret_vals = [ x for x in all_tasks if not is_rhic_lookup_task_expired(x)]
    return ret_vals

def delete_rhic_lookup(lookup_task):
    try:
        _LOG.info("Deleting %s" % (lookup_task))
        # Using 'safe=True' to ensure the delete is executed before returning
        lookup_task.delete(safe=True)
        return True
    except Exception, e:
        _LOG.exception(e)
        return False

def get_current_rhic_lookup_tasks(uuid):
    """
    Returns a valid RHICLookupTask for this 'uuid' if one exists, or None.
    If an older, or invalid RHICLookupTask is found, it will be deleted from the
    database and None will be returned.

    Usage:  A task can be returned which is either in progress or completed,
            check the "completed" value to determine.  Additionally, the 'status_code'
            of the task holds the cached response code.

    @param uuid: uuid of a RHIC
    @return: a valid RHICLookupTask associated to this 'uuid' or None
    @rtype: L{splice.entitlement.models.RHICLookupTask}
    """
    _LOG.info("get_current_rhic_lookup_tasks(rhic_uuid='%s')" % (uuid))
    current_task = RHICLookupTask.objects(uuid=uuid).first()
    if not current_task:
        _LOG.info("Unable to find lookup task '%s', all lookup tasks are: %s" % (uuid, RHICLookupTask.objects()))
        return None
    expired = is_rhic_lookup_task_expired(current_task)
    if expired:
        delete_rhic_lookup(current_task)
        return None
    return current_task

def process_data(data):
    """
    Imports data into mongo, will update documents that have changed, and remove those which have been deleted
    @param data from rhic_serve
    """
    start = time.time()
    _LOG.info("Fetched %s rhics from rhic_serve" % (len(data)))
    consumer_ids = [x["uuid"] for x in data if x.has_key("uuid")]
    # Determine which of these IDs already exist in DB and which are new

    existing_objects = ConsumerIdentity.objects(uuid__in=consumer_ids).only("uuid")
    existing_ids = [str(x.uuid) for x in existing_objects]
    new_consumer_ids = set(consumer_ids).difference(set(existing_ids))
    existing_consumers = [x for x in data if x.has_key("uuid") and x["uuid"] in existing_ids]
    new_consumers = [x for x in data if x.has_key("uuid") and x["uuid"] in new_consumer_ids]
    end_determine_new_and_existing = time.time()
    _LOG.info("%s RHICs from parent consist of %s new and %s updates, %s seconds to determine this" % \
              (len(data), len(new_consumers), len(existing_consumers), end_determine_new_and_existing-start))
    # Perform a bulk insert for all new_consumers
    if new_consumers:
        objectids = bulk_insert(new_consumers)
        if len(objectids) != len(new_consumer_ids):
            _LOG.warning("Some RHICs were not created in database: %s new RHICs were intended only %s were created" % \
                         (len(new_consumers), len(objectids)))
    end_bulk_insert_new_items = time.time()
    # Update existing consumer IDs serially
    if existing_consumers:
        for item in existing_consumers:
            create_or_update_consumer_identity(item)
    end_update_existing_items = time.time()
    _LOG.info("%s seconds to process %s RHICs, %s new (in %s seconds) and %s updated (in %s seconds)" % \
                (end_update_existing_items-start, len(data), len(new_consumers),
                end_bulk_insert_new_items-end_determine_new_and_existing,
                len(existing_consumers), end_update_existing_items-end_bulk_insert_new_items))
    return consumer_ids

def bulk_insert(data):
    # Form model objects out of dictionary data items
    objects = []
    for d in data:
        objects.append(convert_dict_to_consumer_identity(d))
    if objects:
        # Perform bulk insert
        q = ConsumerIdentity.objects()
        return q.insert(objects, load_bulk=False, safe=False)
    return []

def convert_dict_to_consumer_identity(item):
    """
    Converts a dictionary to a ConsumerIdentity
    @param item: dict containing needed info to construct a ConsumerIdentity object
                    required keys: 'uuid', 'engineering_ids'
    @type item: dict
    @return: instance of a consumer identity, note this instance has not yet been saved
    @rtype: splice.entitlement.models.ConsumerIdentity
    """
    if not item.has_key("uuid"):
        raise Exception("Missing required parameter: 'uuid'")
    if not item.has_key("engineering_ids"):
        raise Exception("Missing required parameter: 'engineering_ids'")
    consumer_id = item["uuid"]
    engineering_ids = item["engineering_ids"]

    created_date = datetime.now(tzutc())
    modified_date = datetime.now(tzutc())
    deleted = False
    deleted_date = None
    if item.has_key("created_date"):
        created_date = convert_to_datetime(item["created_date"])
    if item.has_key("modified_date"):
        modified_date = convert_to_datetime(item["modified_date"])
    if item.has_key("deleted"):
        deleted = item["deleted"]
    if item.has_key("deleted_date"):
        deleted_date = convert_to_datetime(item["deleted_date"])
    if deleted and not deleted_date:
        deleted_date = datetime.now(tzutc())

    identity = ConsumerIdentity(uuid=UUID(consumer_id))
    identity.engineering_ids = engineering_ids
    identity.created_date = created_date
    identity.modified_date = modified_date
    identity.deleted = deleted
    identity.deleted_date = deleted_date
    return identity


def create_or_update_consumer_identity(item):
    """
    Creates a new consumer identity or updates existing to match passed in item data
    @param item: dict containing needed info to construct a ConsumerIdentity object
                    required keys: 'uuid', 'engineering_ids'
    @type item: dict
    @return: True on success, False on failure
    @rtype: bool
    """
    if not item.has_key("uuid"):
        raise Exception("Missing required parameter: 'uuid'")
    if not item.has_key("engineering_ids"):
        raise Exception("Missing required parameter: 'engineering_ids'")
    consumer_id = item["uuid"]
    engineering_ids = item["engineering_ids"]

    created_date = datetime.now(tzutc())
    modified_date = datetime.now(tzutc())
    deleted = False
    deleted_date = None
    if item.has_key("created_date"):
        created_date = convert_to_datetime(item["created_date"])
    if item.has_key("modified_date"):
        modified_date = convert_to_datetime(item["modified_date"])
    if item.has_key("deleted"):
        deleted = item["deleted"]
    if item.has_key("deleted_date"):
        deleted_date = convert_to_datetime(item["deleted_date"])
    if deleted and not deleted_date:
        deleted_date = datetime.now(tzutc())

    identity = ConsumerIdentity.objects(uuid=UUID(consumer_id)).first()
    if not identity:
        _LOG.info("Creating new ConsumerIdentity for: %s" % (consumer_id))
        identity = ConsumerIdentity(uuid=UUID(consumer_id))

    identity.engineering_ids = engineering_ids
    identity.created_date = created_date
    identity.modified_date = modified_date
    identity.deleted = deleted
    identity.deleted_date = deleted_date
    try:
        _LOG.debug("Updating ConsumerIdentity: %s" % (identity))
        identity.save(safe=True)
        return True
    except Exception, e:
        _LOG.exception(e)
        return False

def get_last_sync_timestamp(server_hostname):
    key = sanitize_key_for_mongo(server_hostname)
    sync = IdentitySyncInfo.objects(server_hostname=key).first()
    if not sync:
        return None
    return sync.last_sync

def save_last_sync(server_hostname, timestamp):
    key = sanitize_key_for_mongo(server_hostname)
    sync = IdentitySyncInfo.objects(server_hostname=key).first()
    if not sync:
        sync = IdentitySyncInfo(server_hostname=key)
    sync.last_sync = timestamp
    try:
        sync.save()
        _LOG.info("Last sync saved: %s" % (sync))
    except Exception, e:
        _LOG.exception(e)
        return False
    return True

def sync_single_rhic_blocking(uuid):
    cfg = config.get_rhic_serve_config_info()
    _LOG.info("Attempting to synchronize a single RHIC '%s' with config info: '%s'" % (uuid, cfg))
    host = cfg["host"]
    port = cfg["port"]
    # URL is based on URL for 'all_rhics', we add the RHIC uuid to it to form a single URL
    url = cfg["get_all_rhics_url"]
    status_code, data = rhic_serve_client.get_single_rhic(host=host, port=port, url=url, uuid=uuid)
    _LOG.info("Received '%s' from %s:%s:%s for RHIC '%s'. Response = \n%s" % (status_code, host, port, url, uuid, data))
    if status_code == 202:
        # This task is in progress, nothing further to do
        return status_code
    if status_code == 200:
        create_or_update_consumer_identity(data)
    return status_code


def sync_from_rhic_serve_blocking():
    _LOG.info("Attempting to synchronize RHIC data from configured rhic_serve")
    current_time = datetime.now(tzutc())
    cfg = config.get_rhic_serve_config_info()
    # Lookup last time we synced from this host
    # Sync records from that point in time.
    # If we haven't synced before we get back None and proceed with a full sync

    server_hostname = cfg["host"]
    last_sync = get_last_sync_timestamp(server_hostname)
    current_offset=0
    current_limit=cfg["sync_all_rhics_pagination_limit_per_call"]
    sync_loop = True
    while sync_loop:
        data, meta = rhic_serve_client.get_all_rhics(host=server_hostname, port=cfg["port"],
            url=cfg["get_all_rhics_url"], last_sync=last_sync, offset=current_offset, limit=current_limit)
        if not data:
            _LOG.info("Received no data from %s:%s%s" % (cfg["host"], cfg["port"], cfg["get_all_rhics_url"]))
            return True
        _LOG.info("Fetched %s RHICs from %s:%s%s with last_sync=%s, offset=%s, limit=%s" % (len(data),
             cfg["host"], cfg["port"], cfg["get_all_rhics_url"], last_sync, current_offset, current_limit))
        syncd_uuids = process_data(data)
        current_offset = current_offset + len(syncd_uuids)
        if current_offset >= meta["total_count"]:
            break
    if not save_last_sync(server_hostname, current_time):
        _LOG.info("Unable to update last sync for: %s at %s" % (server_hostname, current_time))
        return False
    return True

def sync_from_rhic_serve():
    """
    @return None if a sync is in progress, or a thread id if a new sync has been initiated.
    @rtype: splice.common.identity.SyncRHICServeThread
    """
    # If a sync job is on-going, do nothing, just return and let it finish
    global JOBS
    JOB_LOCK.acquire()
    try:
        key = SyncRHICServeThread.__name__
        if JOBS.has_key(key):
            if not JOBS[key].finished:
                _LOG.info("A sync job from %s is already running, will allow to finish and not start a new sync" % (key))
                # Job is still running so let it finish
                return
        t = SyncRHICServeThread()
        t.start()
        JOBS[key] = t
        return t
    finally:
        JOB_LOCK.release()

class SyncRHICServeThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.finished = False

    def run(self):
        _LOG.info("Running sync from %s" % (self.__class__.__name__))
        try:
            try:
                sync_from_rhic_serve_blocking()
            except Exception, e:
                _LOG.exception(e)
                raise
        finally:
            self.finished = True
            self.remove_reference()
            _LOG.info("Finished sync from %s" % (self.__class__.__name__))

    def remove_reference(self):
        global JOBS
        JOB_LOCK.acquire()
        try:
            key = self.__class__.__name__
            if JOBS.has_key(key):
                del JOBS[key]
        finally:
            JOB_LOCK.release()
