#!/usr/bin/env python
import logging
import logging.config
import os
import random
import string
import time
from uuid import uuid4
from datetime import timedelta
from datetime import datetime
from dateutil.tz import tzutc
from django.conf import settings
from optparse import OptionParser

from splice.common import config, splice_server_client
from splice.common.models import ProductUsage

CONSUMER = str(uuid4())
SPLICE_SERVER = str(uuid4())
# Will hold a list of generated fake instance identifiers
INSTANCE_IDS = []

_LOG = None
def init_logging():
    global _LOG
    log_config_file=os.path.join(os.path.abspath(os.path.dirname(__file__)), "logging_config")
    logging.config.fileConfig(log_config_file, disable_existing_loggers=True)
    _LOG = logging.getLogger(__name__)
    print "Reinitialized logging with: %s" % (log_config_file)

def create_random_facts(num_entries=30, length_of_key=10):
    facts = {}
    for x in range(0, num_entries):
        random_str = ''.join(random.choice(string.letters) for i in xrange(length_of_key))
        facts[random_str] = random_str
    return facts

def create_product_usage(checkin_date, instance_identifier):
    pu = ProductUsage()
    pu.consumer = CONSUMER
    pu.splice_server = SPLICE_SERVER
    pu.instance_identifier = instance_identifier
    pu.allowed_product_info = ["69"]
    pu.unallowed_product_info = []
    pu.facts = create_random_facts()
    pu.date = checkin_date
    return pu

def get_checkin_date(current, max):
    checkin_date = datetime.now(tzutc()) - timedelta(hours=max-current)
    return checkin_date

def create_fake_instance_identifier():
    mac = [ 0x00, 0x24, 0x81,
        random.randint(0x00, 0x7f),
        random.randint(0x00, 0xff),
        random.randint(0x00, 0xff) ]
    return ':'.join(map(lambda x: "%02x" % x, mac))

def create_instance_identifiers(num_instances):
    global INSTANCE_IDS
    for index in range(0, num_instances):
        INSTANCE_IDS.append(create_fake_instance_identifier())
    return INSTANCE_IDS

def get_instance_identifier(index):
    return INSTANCE_IDS[index]

def create_data(num_instances, num_entries):
    # Return ProductUsage objects, created so they have hourly checkins
    # going back 'num' hours ago
    now = datetime.now(tzutc())
    items = []
    for entry_index in range(0, num_entries):
        checkin_date = now - timedelta(hours=num_entries-entry_index)
        for inst_index in range(0, num_instances):
            inst_id = get_instance_identifier(inst_index)
            items.append(create_product_usage(checkin_date, inst_id))
    return items

def send(host, port, url, data):
    # Transfer data to SpliceServer
    resp = splice_server_client.upload_product_usage_data(host, port, url, data)
    print resp


if __name__ == "__main__":
    parser = OptionParser(description="Timing test for uploading ProductUsage data")
    parser.add_option("--host", action="store", help="Hostname for RCS", default="127.0.0.1")
    parser.add_option("--port", action="store", help="Port for RCS", default="443")
    parser.add_option("--num_entries", action="store", help="Number of ProductUsage objects to upload per instance", default="100")
    parser.add_option("--num_instances", action="store", help="Number of instances to simulate", default="20")
    (opts, args) = parser.parse_args()

    host = opts.host
    port = int(opts.port)
    url = '/splice/api/v1/productusage/'
    num_entries = int(opts.num_entries)
    num_instances = int(opts.num_instances)
    config.init(settings.SPLICE_CONFIG_FILE)
    init_logging() # Redo logging config so we can control where we log data for these runs
    create_instance_identifiers(num_instances)
    data = create_data(num_instances, num_entries)
    print "Created %s ProductUsage objects for %s instances each having %s checkins" % (len(data), num_instances, num_entries)
    start = time.time()
    send(host, port, url, data)
    end = time.time()
    print "Took %s seconds to send %s items" % (end-start, len(data))


