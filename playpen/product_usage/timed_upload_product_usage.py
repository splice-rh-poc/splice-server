#!/usr/bin/env python
import logging
import logging.config
import os
import random
import string
import sys
import time
from uuid import uuid4
from datetime import timedelta
from datetime import datetime
from dateutil.tz import tzutc
from django.conf import settings
from optparse import OptionParser

from splice.common import config, splice_server_client, utils
from splice.common.models import ProductUsage

# Requires subscription-manager RPM to be installed
SUB_MGR_PATH = "/usr/share/rhsm"
sys.path.append(SUB_MGR_PATH)
from subscription_manager.facts import Facts

CONSUMER = str(uuid4())
SPLICE_SERVER = str(uuid4())

# Below will be initialized at runtime
INSTANCE_IDS = []
FACTS = []

_LOG = None
def init_logging():
    global _LOG
    log_config_file=os.path.join(os.path.abspath(os.path.dirname(__file__)), "logging_config")
    logging.config.fileConfig(log_config_file, disable_existing_loggers=True)
    _LOG = logging.getLogger(__name__)
    print "Reinitialized logging with: %s" % (log_config_file)

def init_instance_identifiers(num_instances):
    global INSTANCE_IDS
    for index in range(0, num_instances):
        INSTANCE_IDS.append(create_fake_instance_identifier())
    return INSTANCE_IDS

def init_facts(num_instances):
    global FACTS
    for index in range(0, num_instances):
        inst_id = INSTANCE_IDS[index]
        facts = Facts().get_facts()
        facts['net.interface.eth0.mac_address'] = inst_id
        facts = utils.sanitize_dict_for_mongo(facts)
        FACTS.append(facts)
    return FACTS

def create_fake_instance_identifier():
    mac = [ 0x00, 0x24, 0x81,
        random.randint(0x00, 0x7f),
        random.randint(0x00, 0xff),
        random.randint(0x00, 0xff) ]
    return ':'.join(map(lambda x: "%02x" % x, mac))

def create_product_usage(checkin_date, instance_identifier, facts):
    pu = ProductUsage()
    pu.consumer = CONSUMER
    pu.splice_server = SPLICE_SERVER
    pu.instance_identifier = instance_identifier
    pu.allowed_product_info = ["69"]
    pu.unallowed_product_info = []
    pu.facts = facts
    pu.date = checkin_date
    return pu

def create_data(num_instances, num_entries):
    # Return ProductUsage objects, created so they have hourly checkins
    # going back 'num' hours ago
    now = datetime.now(tzutc())
    items = []
    for entry_index in range(0, num_entries):
        checkin_date = now - timedelta(hours=num_entries-entry_index)
        for inst_index in range(0, num_instances):
            inst_id = INSTANCE_IDS[inst_index]
            facts = FACTS[inst_index]
            items.append(create_product_usage(checkin_date, inst_id, facts))
    return items

def send(host, port, url, data, batch_size=5000):
    # Transfer data to SpliceServer
    start_index = 0
    end_index = 0
    while True:
        end_index += batch_size
        if end_index > len(data):
            end_index = len(data)
        sub_data = data[start_index:end_index]
        start = time.time()
        resp = splice_server_client.upload_product_usage_data(host, port, url, sub_data)
        end = time.time()
        print "Sent %s items in %.4f seconds" % (len(sub_data), end-start)
        start_index += batch_size
        if end_index >= len(data):
            break

if __name__ == "__main__":
    parser = OptionParser(description="Timing test for uploading ProductUsage data")
    parser.add_option("--host", action="store", help="Hostname for RCS", default="127.0.0.1")
    parser.add_option("--port", action="store", help="Port for RCS", default="443")
    parser.add_option("--num_entries", action="store", help="Number of ProductUsage objects to upload per instance", default="100")
    parser.add_option("--num_instances", action="store", help="Number of instances to simulate", default="20")
    (opts, args) = parser.parse_args()

    # Parse CLI
    host = opts.host
    port = int(opts.port)
    url = '/splice/api/v1/productusage/'
    num_entries = int(opts.num_entries)
    num_instances = int(opts.num_instances)
    # Init db connection and splice classes
    config.init(settings.SPLICE_CONFIG_FILE)
    init_logging() # Redo logging config so we can control where we log data for these runs
    # Populate system facts
    start_a = time.time()
    init_instance_identifiers(num_instances)
    init_facts(num_instances)
    start_b = time.time()
    # Create checkin data
    data = create_data(num_instances, num_entries)
    end = time.time()
    print "\nCreated %s ProductUsage objects for %s instances each having %s checkins" % (len(data), num_instances, num_entries)
    print "%.3f seconds to create simulated data, %.3f seconds to init system facts, %.3f seconds to generate checkins" % \
            (end-start_a, start_b-start_a, end-start_b)
    start = time.time()
    # Send data to server
    send(host, port, url, data)
    end = time.time()
    print "Took %s seconds to send %s items" % (end-start, len(data))


