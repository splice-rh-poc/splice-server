#!/usr/bin/env python

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "splice.checkin_service.settings")

import logging
import logging.config
import sys
import time
from django.conf import settings
from optparse import OptionParser

from splice.common import config, splice_server_client, utils
from splice.managers import upload
from splice.common.models import ProductUsage

_LOG = None
def init_logging():
    global _LOG
    log_config_file=os.path.join(os.path.abspath(os.path.dirname(__file__)), "logging_config")
    logging.config.fileConfig(log_config_file, disable_existing_loggers=True)
    _LOG = logging.getLogger(__name__)
    print "Reinitialized logging with: %s" % (log_config_file)

if __name__ == "__main__":
    parser = OptionParser(description="Timing test for querying/updating ProductUsage data")
    parser.add_option("--limit", action="store", help="How many items to test with", default="10000")
    (opts, args) = parser.parse_args()

    # Init db connection and splice classes
    config.init(settings.SPLICE_CONFIG_FILE)
    init_logging() # Redo logging config so we can control where we log data for these runs

    limit = int(opts.limit)
    addr = __file__

    a = time.time()
    # Perform a query and get time
    usage_items = upload._get_product_usage_data(addr, limit)
    b = time.time()

    object_ids = [x.id for x in usage_items]
    c = time.time()
    # Test writes
    upload._mark_sent(object_ids, addr)
    d = time.time()

    # Cleanup
    upload._unmark_sent(object_ids, addr)
    e = time.time()

    print "%s seconds to fetch %s items" % (b-a, len(object_ids))
    print "%s seconds to form list of object ids for %s items" % (c-b, len(object_ids))
    print "%s seconds to update tracker for %s items" % (d-c, len(object_ids))
    print "%s seconds to remove entry from tracker for %s items" % (e-d, len(object_ids))
