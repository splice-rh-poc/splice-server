#!/usr/bin/env python

import mongoengine
import uuid
from optparse import OptionParser

from splice.entitlement.models import ConsumerIdentity

MONGO_DATABASE_NAME = 'checkin_service'

def init():
    mongoengine.connect(MONGO_DATABASE_NAME)
    mongoengine.register_connection("rhic_serve", MONGO_DATABASE_NAME)

def create_identities(num_rhics):
    objects = []
    for x in range(0, num_rhics):
        identity = ConsumerIdentity(uuid=uuid.uuid4())
        identity.engineering_ids=[str(x)]
        objects.append(identity)
    q = ConsumerIdentity.objects()
    return q.insert(objects, safe=False, load_bulk=False)

if __name__ == "__main__":
    parser = OptionParser(description="Test script to generate many fake RHICs")
    parser.add_option("--num", action="store", 
            help="Number of RHICs to create", default=10000)
    (opts, args) = parser.parse_args()
    num_rhics = int(opts.num)
    init()
    # How many RHICs to create? parse CLI options
    # Create RHICs
    print "Will create %s RHICs into DB: %s" % (num_rhics, MONGO_DATABASE_NAME)
    created_ids = create_identities(num_rhics)
    print "Created %s RHICs" % (len(created_ids))
