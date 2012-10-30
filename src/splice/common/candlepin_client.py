# -*- coding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

# Responsible for making a remote call to candlepin and retrieve an entitlement certificate

import base64
import httplib
import json
import logging
import time
import urllib
from django.conf import settings

from splice.common import config
from splice.common.exceptions import RequestException

_LOG = logging.getLogger(__name__)

def get_entitlement(host, port, url, requested_products, identity,
                    username, password,
                    start_date=None, end_date=None,
                    debug=False):
    """

    @param host: entitlement server host address
    @param port: entitlement server host port
    @param url:  URL to access entitlement service
    @param requested_products: list of engineering product ids
    @type requested_products: [str]
    @param identity: identity we are requesting an ent cert on behalf of
    @type identity: checkin_service.common.models.ConsumerIdentity
    @param username: username for auth to entitlement service
    @param password: password for auth to entitlement service
    @param start_date:  optional param, if specified controls start date of certificate
                        expected to be in isoformat as: datetime.datetime.now().isoformat()
    @param end_date:    optional param, if specified controls end date of certificate
                        expected to be in isoformat similar to 'start_date'
    @param debug:       optional param, default to False, if True will print more debug information
    @return:
    """
    status, data = _request(host, port, url,
        requested_products, identity,
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

def _request(host, port, url, requested_products,
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
        "product": requested_products,
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
    import pytz
    config.init(settings.SPLICE_CONFIG_FILE)
    cfg = config.get_candlepin_config_info()

    start_date = datetime.datetime.now(tz=pytz.utc)
    end_date = (start_date + datetime.timedelta(minutes=15))
    print "Start Date: %s" % (start_date.isoformat())
    print "End Date: %s" % (end_date.isoformat())
    certs =  get_entitlement(host=cfg["host"], port=cfg["port"], url=cfg["url"],
        requested_products=["69","83"],
        identity="1234",
        username=cfg["username"], password=cfg["password"],
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        debug=True)
    print "---\n\n"
    print "certs = \n%s" % (certs)
