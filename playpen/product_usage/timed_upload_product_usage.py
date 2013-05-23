#!/usr/bin/env python
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "splice.checkin_service.settings")

import logging
import logging.config
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
from splice.common.models import MarketingProductUsage

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

def create_marketing_product_usage(checkin_date, instance_identifier, facts):
    mpu = MarketingProductUsage()
    mpu.splice_server = SPLICE_SERVER
    mpu.instance_identifier = instance_identifier
    mpu.facts = facts
    mpu.checkin_date = checkin_date
    return mpu

def create_data(num_instances, num_entries, begin):
    # Return MarketingProductUsage objects, created so they have hourly checkins
    # going back 'num' hours ago
    now = datetime.now(tzutc())
    items = []
    for entry_index in range(0, num_entries):
        checkin_date = begin - timedelta(hours=num_entries-entry_index)
        for inst_index in range(0, num_instances):
            inst_id = INSTANCE_IDS[inst_index]
            facts = FACTS[inst_index]
            items.append(create_marketing_product_usage(checkin_date, inst_id, facts))
    return items

def send(host, port, url, data, batch_size=5000, gzip_body=False):
    # Transfer data to SpliceServer
    start_index = 0
    end_index = 0
    while True:
        end_index += batch_size
        if end_index > len(data):
            end_index = len(data)
        sub_data = data[start_index:end_index]
        start = time.time()
        resp = splice_server_client.upload_product_usage_data(host, port, url, {"objects": sub_data}, gzip_body=gzip_body)
        end = time.time()
        print "Sent %s items in %.4f seconds" % (len(sub_data), end-start)
        start_index += batch_size
        if end_index >= len(data):
            break

def translate_date(input):
    date_object = datetime.strptime(i, '%Y-%m-%d')

if __name__ == "__main__":
    parser = OptionParser(description="Timing test for uploading ProductUsage data")
    parser.add_option("--host", action="store", help="Hostname for RCS", default="127.0.0.1")
    parser.add_option("--port", action="store", help="Port for RCS", default="443")
    parser.add_option("--begin", action="store", help="Begin date to create entries from, format: YYYY-MM-DD", default=None)
    parser.add_option("--num_entries", action="store", help="Number of ProductUsage objects to upload per instance", default="1")
    parser.add_option("--num_instances", action="store", help="Number of instances to simulate", default="1")
    parser.add_option("--nogzip", action="store_true", help="Do not GZip the request body", default=False)
    (opts, args) = parser.parse_args()

    # Parse CLI
    host = opts.host
    port = int(opts.port)
    url = '/splice/api/v1/marketingproductusage/'
    num_entries = int(opts.num_entries)
    num_instances = int(opts.num_instances)
    gzip_body = not opts.nogzip

    begin = datetime.now(tzutc())
    if opts.begin:
        try:
            begin = datetime.strptime(opts.begin, '%Y-%m-%d')
        except Exception, e:
            print "Unable to parse: %s" % (opts.begin)
            print "Caught exception: %s" % (e)
            sys.exit(1)
        begin = begin.replace(tzinfo=tzutc())
    print "Will create %s entries for %s instances beginning at: %s" % (num_entries, num_instances, begin)
    # Init db connection and splice classes
    config.init(settings.SPLICE_CONFIG_FILE)
    init_logging() # Redo logging config so we can control where we log data for these runs
    # Populate system facts
    start_a = time.time()
    init_instance_identifiers(num_instances)
    init_facts(num_instances)
    start_b = time.time()
    # Create checkin data
    data = create_data(num_instances, num_entries, begin=begin)
    end = time.time()
    print "\nCreated %s MarketingProductUsage objects for %s instances each having %s checkins" % (len(data), num_instances, num_entries)
    print "%.3f seconds to create simulated data, %.3f seconds to init system facts, %.3f seconds to generate checkins" % \
            (end-start_a, start_b-start_a, end-start_b)
    start = time.time()
    # Send data to server
    send(host, port, url, data, gzip_body=gzip_body)
    end = time.time()
    print "Took %s seconds to send %s items" % (end-start, len(data))


