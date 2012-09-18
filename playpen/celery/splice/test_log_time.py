#!/usr/bin/env python
import time
from splice.entitlement.tasks import log_time

result = log_time.delay()
while not result.ready():
    print "Sleeping...waiting for result"
    time.sleep(1)
print "Task yield result of: %s" % (result.result)


