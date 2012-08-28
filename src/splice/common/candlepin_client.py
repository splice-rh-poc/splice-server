# Responsible for making a remote call to candlepin and retrieve an entitlement certificate

import base64
import httplib
import json
import logging
import time
import urllib

from splice.common import config
from splice.common.exceptions import RequestException

_LOG = logging.getLogger(__name__)

def get_entitlement(host, port, url, installed_products, identity,
                    username, password, debug=False):
    status, data = _request(host, port, url, installed_products, identity,
        username, password, debug)
    if status == 200:
        return parse_data(data)
    raise RequestException(status, data)

def parse_data(data):
    certs = []
    for d in data["certificates"]:
        item = (d["cert"], d["key"], d["serial"]["serial"])
        certs.append(item)
    return certs

def _request(host, port, url, installed_products,
                identity, username, password, debug=False):
    connection = httplib.HTTPConnection(host, port)
    if debug:
        connection.set_debuglevel(100)
    method = 'GET'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    raw = ':'.join((username, password))
    encoded = base64.encodestring(raw)[:-1]
    headers['Authorization'] = 'Basic ' + encoded

    query_params = {
        "productIDs": installed_products,
        "rhicUUID": identity,
    }
    data = urllib.urlencode(query_params)
    url = url +"?" + data
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
            output = open("example_candlepin_data_%s.json" % (time.time()), "w")
            output.write(response_body_raw)
            output.close()
    return response.status, response_body


if __name__ == "__main__":
    config.init()
    cfg = config.get_candlepin_config_info()

    print get_entitlement(host=cfg["host"], port=cfg["port"], url=cfg["url"],
        installed_products=["37060","37061"],
        identity="1234",
        username=cfg["username"], password=cfg["password"], debug=True)
