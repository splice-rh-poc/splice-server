#!/usr/bin/env python
import isodate
import logging
import logging.config
import mongoengine
import os
import time
import uuid as module_uuid

from datetime import datetime
from dateutil.tz import tzutc
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
    mongoengine.connection.disconnect()
    global DB_CONNECTION
    DB_CONNECTION = mongoengine.connection.connect(MONGO_DATABASE_NAME)
    mongoengine.register_connection("rhic_serve", MONGO_DATABASE_NAME)
    DB_CONNECTION.drop_database(MONGO_DATABASE_NAME)

def get_single_entry(uuid=None, created_date=None, modified_date=None, engineering_ids=None):
    data = {}
    if not created_date:
        created_date = str(isodate.datetime_isoformat(datetime.now(tzutc())))
    data["created_date"] = str(created_date)
    if not modified_date:
        modified_date = str(isodate.datetime_isoformat(datetime.now(tzutc())))
    data["modified_date"] = str(modified_date)
    if engineering_ids is None:
        engineering_ids = ["1", "2", "3", "4", "5"]
    data["engineering_ids"] = engineering_ids
    if not uuid:
        uuid = str(module_uuid.uuid4())
    data["uuid"] = uuid
    return data

def convert_to_raw_data(ids):
    raw_data = []
    for consumer_uuid in ids:
        obj = ConsumerIdentity.objects(uuid=consumer_uuid).first()
        d = get_single_entry(uuid=str(obj.uuid), created_date=str(obj.created_date),
                modified_date=str(obj.modified_date),
                engineering_ids=obj.engineering_ids)
        raw_data.append(d)
    return raw_data

def get_raw_data(num_rhics):
    data = []
    for x in range(0, num_rhics):
        data.append(get_single_entry())
    return data

def get_saved_uuids(num_rhics):
    saved_uuids = []
    for x in range(0, num_rhics):
        identity = ConsumerIdentity(uuid=module_uuid.uuid4())
        identity.engineering_ids=["1","2","3"]
        identity.save()
        saved_uuids.append(identity.uuid)
    return saved_uuids

def _sync(data):
    return identity.process_data(data)

if __name__ == "__main__":
    parser = OptionParser(description="Test script to time update/insert of RHICs")
    parser.add_option("--num", action="store", 
            help="Number of RHICs to test with", default=10)
    (opts, args) = parser.parse_args()
    num_rhics = int(opts.num)
    init()

    data = get_raw_data(num_rhics)
    start = time.time()
    _sync(data)
    end = time.time()
    print "%s seconds to sync %s rhics that are all new" % (end-start, num_rhics)
    clean_db()

    saved_uuids = get_saved_uuids(num_rhics)
    raw_data = convert_to_raw_data(saved_uuids)
    start = time.time()
    _sync(raw_data)
    end = time.time()
    print "%s seconds to sync %s rhics that are all updated" % (end-start, num_rhics)
    clean_db()
