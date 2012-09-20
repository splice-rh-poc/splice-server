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
from threading import Thread, Lock
from uuid import UUID

from datetime import datetime
from dateutil.tz import tzutc

from splice.common import config
from splice.common import rhic_serve_client
from splice.common.utils import convert_to_datetime
from splice.entitlement.models import ConsumerIdentity

_LOG = logging.getLogger(__name__)

JOBS = {}
JOB_LOCK = Lock()


def process_data(data):
    """
    Imports data into mongo, will update documents that have changed, and remove those which have been deleted
    @param data from rhic_serve
    """
    # TODO: Redo this logic so it supports batch lookups and is more efficient
    "Fetched %s rhics from rhic_serve" % (len(data))
    for item in data:
        _LOG.debug("Processing: %s" % (item))
        create_or_update_consumer_identity(item)
    ###
    # TODO: Consider removing this 'removal' logic when getting ready to deploy in production
    #   Does it make sense to keep this, or should we remove it?
    # Process RHICs that have been removed from the remote source
    # This removal is likely to be more for testing as we delete database and cleanup environments
    # In production we plan to keep 'deleted' RHICs by marking them as deleted.
    ###
    objects = ConsumerIdentity.objects()
    known_uuids = [str(x.uuid) for x in objects]
    remote_uuids = [x["uuid"] for x in data]
    known_uuids = set(known_uuids)
    remote_uuids = set(remote_uuids)
    uuids_to_remove = known_uuids.difference(remote_uuids)
    for old_uuid in uuids_to_remove:
        _LOG.info("Removing: %s" % (old_uuid))
        ci = ConsumerIdentity.objects(uuid=UUID(old_uuid))
        ci.delete()

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


def sync_from_rhic_serve_blocking():
    _LOG.info("Attempting to synchronize RHIC data from configured rhic_serve")
    cfg = config.get_rhic_serve_config_info()
    # TODO need to implement pagination
    data = rhic_serve_client.get_all_rhics(host=cfg["host"], port=cfg["port"], url=cfg["get_all_rhics_url"])
    if not data:
        _LOG.info("Received no data from %s:%s%s" % (cfg["host"], cfg["port"], cfg["get_all_rhics_url"]))
        return
    _LOG.info("Fetched %s RHICs from %s:%s%s" % (len(data), cfg["host"], cfg["port"], cfg["get_all_rhics_url"]))
    process_data(data)

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
