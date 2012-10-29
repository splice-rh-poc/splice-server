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
from optparse import OptionParser

from splice.common import config, splice_server_client
from splice.common.models import ProductUsage

CONSUMER = str(uuid4())
SPLICE_SERVER = str(uuid4())
INSTANCE_IDENTIFIER = "A0:A0:A0:A0:00:A0"

LOG_CONFIG_FILE=os.path.join(os.path.abspath(os.path.dirname(__file__)), "logging_config")
logging.config.fileConfig(LOG_CONFIG_FILE)
_LOG = logging.getLogger(__name__)

def create_random_facts(num_entries=30, length_of_key=10):
    facts = {}
    for x in range(0, num_entries):
        random_str = ''.join(random.choice(string.letters) for i in xrange(length_of_key))
        facts[random_str] = random_str
    return facts

def create_product_usage(checkin_date):
    pu = ProductUsage()
    pu.consumer = CONSUMER
    pu.splice_server = SPLICE_SERVER
    pu.instance_identifier = INSTANCE_IDENTIFIER
    pu.allowed_product_info = ["1", "2", "3", "4"]
    pu.unallowed_product_info = ["100"]
    pu.facts = create_random_facts()
    pu.date = checkin_date
    return pu

def get_checkin_date(current, max):
    checkin_date = datetime.now(tzutc()) - timedelta(hours=max-current)

def create_data(num):
    # Return ProductUsage objects, created so they have hourly checkins
    # going back 'num' hours ago
    now = datetime.now(tzutc())
    items = []
    for index in range(0, num):
        checkin_date = now - timedelta(hours=num-index)
        items.append(create_product_usage(checkin_date))
    return items

def send(host, port, url, data):
    # Transfer data to SpliceServer
    resp = splice_server_client.upload_product_usage_data(host, port, url, data)
    print resp


if __name__ == "__main__":
    parser = OptionParser(description="Timing test for uploading ProductUsage data")
    parser.add_option("--host", action="store", help="Hostname for RCS", default="127.0.0.1")
    parser.add_option("--port", action="store", help="Port for RCS", default="443")
    parser.add_option("--num", action="store", help="Number of ProductUsage objects to upload", default="100")
    (opts, args) = parser.parse_args()

    host = opts.host
    port = int(opts.port)
    url = '/splice/api/v1/productusage/'
    num = int(opts.num)
    config.init()
    data = create_data(num)
    print "Created %s ProductUsage objects" % (len(data))
    start = time.time()
    send(host, port, url, data)
    end = time.time()
    print "Took %s seconds to send %s items" % (end-start, len(data))


