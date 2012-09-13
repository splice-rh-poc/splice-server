#from __future__ import absolute_import

from celery import Celery
#from proj import celeryconfig
#import celeryconfig

celery = Celery("proj.tasks")
celery.config_from_object('celeryconfig')

@celery.task(name="test_project.tasks.add")
def add(x, y):
    return x + y


@celery.task(name="test_project.tasks.mul")
def mul(x, y):
    return x * y


@celery.task(name="test_project.tasks.xsum")
def xsum(numbers):
    return sum(numbers)
