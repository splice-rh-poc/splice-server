#!/usr/bin/env python
import logging
import logging.config
import os

from optparse import OptionParser

from splice.common import rhic_serve_client

LOG_CONFIG_FILE=os.path.join(os.path.abspath(os.path.dirname(__file__)), "logging_config")
logging.config.fileConfig(LOG_CONFIG_FILE)


def fetch(hostname, num_rhics, gzip_support=True, offset=0, port=443, url="/splice/api/v1/rhicrcs/"):
    data, meta = rhic_serve_client.get_all_rhics(host=hostname, port=port, url=url, 
        offset=offset, limit=num_rhics, debug=False, accept_gzip=gzip_support)
    return data, meta

if __name__ == "__main__":
    parser = OptionParser(description="Test script to fetch RHICs from RCS")
    parser.add_option("--num", action="store", default=10,
            help="Number of RHICs to test with")
    parser.add_option("--offset", action="store", default=0,
            help="Offset of where to start rhic fetch from")
    parser.add_option("--zip", action="store_true", default=False,
            help="If set, will disable gzip support")
    parser.add_option("--host", action="store", default="localhost",
            help="hostname of RCS")
    (opts, args) = parser.parse_args()
    num_rhics = int(opts.num)
    offset = int(opts.offset)
    gzip_support = opts.zip
    hostname = opts.host

    data, meta = fetch(hostname, num_rhics, gzip_support, offset)
    print "Fetched %s rhics" % (len(data))
    print "Received meta data: %s" % (meta)

