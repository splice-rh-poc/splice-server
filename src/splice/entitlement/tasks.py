# Placeholder for celery tasks
from celery import Celery
from splice.common import celeryconfig

BASE_TASK_NAME="splice.entitlement.tasks"
celery = Celery(BASE_TASK_NAME)
celery.config_from_object(celeryconfig)

@celery.task(name="%s.add" % (BASE_TASK_NAME))
def add(x, y):
    return x + y

@celery.task(name="%s.mul" % BASE_TASK_NAME)
def mul(x, y):
    return x * y

@celery.task(name="%s.xsum" % BASE_TASK_NAME)
def xsum(numbers):
    return sum(numbers)