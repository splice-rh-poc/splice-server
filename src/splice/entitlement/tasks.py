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
def sync_rhics(server_info=None):
    """
    Will synchronize RHIC to product mapping data from a RCS server.

    @param server_info: optional, dict of information to connect to RCS server
                        if no dict specified will retrieve info from local config file
    @type  server_info: {}
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
