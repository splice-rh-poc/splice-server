import logging
from threading import Thread, Lock
from uuid import UUID

from splice.common import config
from splice.common import rhic_serve_client
from splice.entitlement.models import ConsumerIdentity

_LOG = logging.getLogger(__name__)

JOBS = {}
JOB_LOCK = Lock()


def process_data(data):
    """
    Imports data into mongo, will update documents that have changed, and remove those which have been deleted

    @param data from rhic_serve in the format: [{"engineering_ids":["str_id"], "uuid":"str_id"}]
    @type [{"engineering_ids":[], "uuid":""}]
    """
    # TODO: Redo this logic so it supports batch lookups and is more efficient
    "Fetched %s rhics from rhic_serve" % (len(data))
    for item in data:
        _LOG.info("Processing: %s" % (item))
        engineering_ids = item["engineering_ids"]
        consumer_id = item["uuid"]
        identity = ConsumerIdentity.objects(uuid=UUID(consumer_id)).first()
        if not identity:
            create_new_consumer_identity(consumer_id, engineering_ids)
            continue
        try:
            _LOG.info("Trying to save: %s" % (identity))
            identity.engineering_ids = engineering_ids
            identity.save()
            _LOG.info("Saved: %s" % (identity))
        except Exception, e:
            _LOG.exception(e)
    # Process RHICs that have been removed from the remote source
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

def create_new_consumer_identity(consumer_id, engineering_ids):
    _LOG.info("Creating new ConsumerIdentity(consumer_id=%s, engineering_ids=%s)" % (consumer_id, engineering_ids))
    identity = ConsumerIdentity(uuid=UUID(consumer_id), engineering_ids=engineering_ids)
    try:
        identity.save(safe=True)
    except Exception, e:
        _LOG.exception(e)

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
