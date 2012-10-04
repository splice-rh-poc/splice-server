#!/usr/bin/env python

import logging
import logging.config
import os
import mongoengine
import time
import uuid

from optparse import OptionParser

from splice.common import identity
from splice.entitlement.models import ConsumerIdentity

LOG_CONFIG_FILE=os.path.join(os.path.abspath(os.path.dirname(__file__)), "logging_config")
logging.config.fileConfig(LOG_CONFIG_FILE)

MONGO_DATABASE_NAME = 'checkin_service_timing_test'
DB_CONNECTION = None

def clean_db():
    DB_CONNECTION.drop_database(MONGO_DATABASE_NAME)

def init():
    global DB_CONNECTION
    DB_CONNECTION = mongoengine.connection.connect(MONGO_DATABASE_NAME)
    mongoengine.register_connection("rhic_serve", MONGO_DATABASE_NAME)
    DB_CONNECTION.drop_database(MONGO_DATABASE_NAME)
    
def simulate_updates(objects):
    for obj in objects:
        obj.engineering_ids.append("999")
        obj.save()
    return objects

def simulate_inserts(num_rhics):
    consumer_ids = []
    for x in range(0, num_rhics):
        identity = ConsumerIdentity(uuid=uuid.uuid4())
        identity.save()
        consumer_ids.append(uuid)
    return consumer_ids

def simulate_inserts_bulk(num_rhics):
    objects = []
    for x in range(0, num_rhics):
        identity = ConsumerIdentity(uuid=uuid.uuid4())
        objects.append(identity)
    q = ConsumerIdentity.objects()
    q.insert(objects, load_bulk=False, safe=False)
    return objects

if __name__ == "__main__":
    parser = OptionParser(description="Test script to time update/insert of RHICs")
    parser.add_option("--num", action="store", 
            help="Number of RHICs to test with", default=10)
    (opts, args) = parser.parse_args()
    num_rhics = int(opts.num)
    init()

    start = time.time()
    simulate_inserts(num_rhics)
    end = time.time()
    count = ConsumerIdentity.objects().count()
    if count != num_rhics:
        print "Error with test, only found %s items in mongo, expected %s" % \
                (count, num_rhics)
        sys.exit(1)
    print "%s seconds to simulate insert of %s RHICs" % (end-start, num_rhics)
    clean_db()

    start = time.time()
    objects = simulate_inserts_bulk(num_rhics)
    end = time.time()
    print "%s seconds to simulate bulk insert of %s RHICs" % (end-start, num_rhics)
    clean_db()

    start = time.time()
    objects = simulate_updates(objects)
    end = time.time()
    print "%s seconds to update %s RHICs" % (end-start, len(objects))


