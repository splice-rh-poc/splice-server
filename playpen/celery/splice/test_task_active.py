#!/usr/bin/env python
import time
from celery.result import AsyncResult

from splice.managers import identity_lookup

def test():
    # Create a task
    uuid = "fb647f68-aa01-4171-b62b-35c2984a5328"
    lookup_task = identity_lookup.create_rhic_lookup_task(uuid)
    print "Lookup Task: %s" % (lookup_task)
    task_id = lookup_task.task_id
    result = AsyncResult(task_id)
    #result = tasks.sync_single_rhic.apply_async((uuid,))
    print "result.state = %s" % (result.state)
    print "Wait 15 seconds"
    time.sleep(15)
    result = AsyncResult(task_id)
    print "Result: result.state = %s" % (result.state)
    
if __name__ == "__main__":
    test()
