#!/usr/bin/env python
import json
import sys

from optparse import OptionParser
from splice.common import config, splice_server_client

def read_file(input_file):
    f = open(input_file)
    try:
        return f.read()
    finally:
        f.close()

def upload(host, port, data):
    return splice_server_client.upload_splice_server_metadata(host, port, "/splice/api/v1/spliceserver/", data)

if __name__ == "__main__":
    # Parse arguments
    parser = OptionParser(description="Seeds a RCS with Splice Server metadata")
    parser.add_option("--host", action="store", help="Hostname for RCS", default="127.0.0.1")
    parser.add_option("--port", action="store", help="Port for RCS", default="443")
    parser.add_option("--input", action="store", help="JSON file containing splice server metadata to upload to server", default="")
    parser.add_option("--config", action="store", help="RCS server config file, defaults to /etc/splice/conf.d/server.conf", 
        default="/etc/splice/conf.d/server.conf")

    (opts, args) = parser.parse_args()
    config.init(opts.config)

    if not opts.input:
        print "Please re-run with --input specified for a JSON file to upload to server"
        sys.exit(1)

    # Read in config file
    data = read_file(opts.input)
    try:
        data = json.loads(data)
    except Exception, e:
        print "Input data from %s does not appear to be valid JSON." % (opts.input)
        print "Input data: \n%s" % (data)
        print "Caught Exception: %s" % (e)
        sys.exit(1)

    # Send to RCS
    print "Data = \n%s" % (data)
    response = upload(opts.host, opts.port, data)
    #print "Uploaded: \n%s\n\nReceived Reponse:\n%s" % (data, response)




