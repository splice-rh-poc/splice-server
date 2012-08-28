# Responsible for making a remote call to rhic_serve to fetch data for RHIC to Product mapping
#
import httplib
import json
import logging
import time

from splice.common import config
from splice.common.exceptions import RequestException

_LOG = logging.getLogger(__name__)

def get_all_rhics(host, port, url, debug=False):
    status, data = _request(host, port, url, debug)
    if status == 200:
        return data
    raise RequestException(status, data)

def _request(host, port, url, debug=False):
    connection = httplib.HTTPConnection(host, port)
    if debug:
        connection.set_debuglevel(100)
    method = 'GET'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    _LOG.info("Sending HTTP request to: %s:%s%s with headers:%s" % (host, port, url, headers))
    connection.request(method, url, body=None, headers=headers)

    response = connection.getresponse()
    response_body = response.read()
    if response.status == 200:
        response_body_raw = response_body
        response_body = json.loads(response_body_raw)
        if debug:
            print "Response: %s %s" % (response.status, response.reason)
            print "JSON: %s" % (json.dumps(response_body))
            output = open("example_rhic_serve_data_%s.json" % (time.time()), "w")
            output.write(response_body_raw)
            output.close()
    return response.status, response_body

if __name__ == "__main__":
    config.init()
    cfg = config.get_rhic_serve_config_info()
    print get_all_rhics(host=cfg["host"], port=cfg["port"], url=cfg["get_all_rhics_url"], debug=True)
