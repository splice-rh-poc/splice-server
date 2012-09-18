#!/usr/bin/env python
import time
from splice.entitlement.tasks import sync_rhics

print "Calling sync_rhics()"
result = sync_rhics.delay()
while not result.ready():
    print "Sleeping...waiting for result"
    time.sleep(1)
print "Task yield result of: %s" % (result.result)


