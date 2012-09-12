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
                    username, password,
                    start_date=None, end_date=None,
                    debug=False):
    """

    @param host:
    @param port:
    @param url:
    @param installed_products:
    @param identity:
    @param username:
    @param password:
    @param start_date:  optional param, if specified controls start date of certificate
                        expected to be in isoformat as: datetime.datetime.now().isoformat()
    @param end_date:    optional param, if specificed controls end date of certificate
                        expected to be in isoformat similar to 'start_date'
    @param debug:       optional param, default to False, if True will print more debug information
    @return:
    """
    status, data = _request(host, port, url,
        installed_products, identity,
        username, password,
        start_date=start_date, end_date=end_date, debug=debug)
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
                identity, username, password,
                start_date=None, end_date=None,
                debug=False):
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

    data = urllib.urlencode(query_params, True)
    url = url +"?" + data
    if start_date and end_date:
        url += "&start=%s&end=%s" % (urllib.quote_plus(start_date),
                                     urllib.quote_plus(end_date))

    _LOG.info("Sending HTTP request to: %s:%s%s with headers:%s" % (host, port, url, headers))
    connection.request(method, url, body=None, headers=headers)

    response = connection.getresponse()
    response_body = response.read()
    if response.status != 200:
        _LOG.info("Response status '%s', '%s', '%s'" % (response.status, response.reason, response_body))
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
    import datetime
    config.init()
    cfg = config.get_candlepin_config_info()

    start_date = datetime.datetime.now()
    end_date = (start_date + datetime.timedelta(minutes=15))
    print "Start Date: %s" % (start_date.isoformat())
    print "End Date: %s" % (end_date.isoformat())
    print get_entitlement(host=cfg["host"], port=cfg["port"], url=cfg["url"],
        installed_products=["69","83"],
        identity="1234",
        username=cfg["username"], password=cfg["password"],
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        debug=True)
