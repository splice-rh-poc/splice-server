# Placeholder for celery tasks
import sys
sys.path.append("/etc/splice/celery")
from celery import Celery

from splice.common.constants import SPLICE_ENTITLEMENT_BASE_TASK_NAME
from splice.common.identity import sync_from_rhic_serve_blocking
import celeryconfig


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

@celery.task(name="%s.sync_rhics")
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
    return sync_from_rhic_serve_blocking()


