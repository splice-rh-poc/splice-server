# Placeholder for celery tasks
import sys
sys.path.append("/etc/splice/celery")
from celery import Celery

from splice.common.constants import SPLICE_ENTITLEMENT_BASE_TASK_NAME
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