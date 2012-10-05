#!/usr/bin/env python
import logging
import logging.config
import os

from splice.common import rhic_serve_client

LOG_CONFIG_FILE=os.path.join(os.path.abspath(os.path.dirname(__file__)), "logging_config")
logging.config.fileConfig(LOG_CONFIG_FILE)

host = "localhost"
port = "443"
url = "/splice/api/v1/rhicrcs/"

data, meta = rhic_serve_client.get_all_rhics(host=host, port=port, url=url, 
        offset=0, limit=1000, debug=False, accept_gzip=True)
print "Fetched %s rhics" % (len(data))
print "Received meta data: %s" % (meta)

