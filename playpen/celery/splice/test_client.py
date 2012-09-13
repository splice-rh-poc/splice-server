#!/usr/bin/env python
import time
from splice.entitlement.tasks import add

x = 4
y = 5

print "Calling add(%s, %s)" % (x, y)
result = add.delay(x, y)
while not result.ready():
    print "Sleeping...waiting for result"
    time.sleep(1)
print "Task yield result of: %s" % (result.result)


