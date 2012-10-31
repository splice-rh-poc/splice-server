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

import httplib
import json
import logging
import time

from django.conf import settings

from splice.common import certs, config, utils
from splice.common.exceptions import RequestException

_LOG = logging.getLogger(__name__)


def parse_data(data):
    # Placeholder, may want to parse response and identify objects that weren't successfully uploaded
    # Returns a list of objects to retry or an empty list on success
    return []

def upload_product_usage_data(host, port, url, pu_data, debug=False):
    key_file = certs.get_splice_server_identity_key_path()
    cert_file = certs.get_splice_server_identity_cert_path()
    serialized_data = utils.obj_to_json(pu_data)
    try:
        status, data = _request(host, port, url, serialized_data, debug=debug, key_file=key_file, cert_file=cert_file)
        if status in [200, 202]:
            return parse_data(data)
    except Exception, e:
        _LOG.exception("Caught exception attempting to send %s product usage objects to %s:%s/%s with key=%s, cert=%s" % \
                       (len(pu_data), host, port, url, key_file, cert_file))
        raise
    raise RequestException(status, data)

def _request(host, port, url, body, debug=False, key_file=None, cert_file=None):
    connection = httplib.HTTPSConnection(host, port, key_file=key_file, cert_file=cert_file)
    if debug:
        connection.set_debuglevel(100)
    method = 'POST'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    _LOG.info("Sending HTTP request with (key=%s, cert=%s) to: %s:%s%s with headers:%s" % (key_file, cert_file, host, port, url, headers))
    connection.request(method, url, body=body, headers=headers)

    response = connection.getresponse()
    response_body = response.read()
    if response.status not in  [200, 202]:
        _LOG.info("Response status '%s', '%s', '%s'" % (response.status, response.reason, response_body))
    if response.status in [httplib.CONFLICT]:
        response_body_raw = response_body
        response_body = json.loads(response_body_raw)
        if debug:
            print "Response: %s %s" % (response.status, response.reason)
            print "JSON: %s" % (json.dumps(response_body))
            output = open("example_splice_server_client_%s.json" % (time.time()), "w")
            output.write(response_body_raw)
            output.close()
    return response.status, response_body

if __name__ == "__main__":
    from datetime import datetime
    from dateutil.tz import tzutc
    from splice.common.models import ProductUsage

    # Create a dummy product usage object
    pu = ProductUsage()
    pu.consumer = "test_consumer"
    pu.splice_server = "test_splice_server"
    pu.instance_identifier = "test_instance_identifier"
    pu.allowed_product_info = ["1", "2", "3", "4"]
    pu.unallowed_product_info = ["100"]
    pu.facts = {"tbd": "values"}
    pu.date = datetime.now(tzutc())

    config.init(settings.SPLICE_CONFIG_FILE)
    cfg = config.get_reporting_config_info()
    remote_server = cfg["servers"][0]
    host = remote_server[0]
    port = remote_server[1]
    url = remote_server[2]

    resp = upload_product_usage_data(host, port, url, [pu], debug=True)
    print "---\n\n"
    print "Response:\n%s" % (resp)
