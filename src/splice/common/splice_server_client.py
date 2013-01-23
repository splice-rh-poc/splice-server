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

from splice.common import certs, config
from splice.common.connect import BaseConnection
from splice.common.exceptions import RequestException

_LOG = logging.getLogger(__name__)

def get_connection(host, port, cert, key, accept_gzip=False):
    # Note: this method will be mocked out in unit tests
    return BaseConnection(host, port, handler="", https=True, cert_file=cert, key_file=key, accept_gzip=accept_gzip)

def send_data(host, port, url, data, accept_gzip=False, gzip_body=False):
    key_file = certs.get_splice_server_identity_key_path()
    cert_file = certs.get_splice_server_identity_cert_path()
    try:
        conn = get_connection(host, port, cert_file, key_file, accept_gzip)
        status, data = conn.POST(url, data, gzip_body=gzip_body)
        return status, data
    except Exception, e:
        _LOG.exception("Caught exception attempting to send data to %s:%s/%s with key=%s, cert=%s" %\
                   (host, port, url, key_file, cert_file))
        raise

def upload_splice_server_metadata(host, port, url, metadata):
    metadata = {"objects":metadata}
    status, data = send_data(host, port, url, metadata)
    if status not in [200, 202, 204]:
        raise RequestException(status, data)
    return status, data

def upload_product_usage_data(host, port, url, pu_data, accept_gzip=False, gzip_body=False):
    status, data = send_data(host, port, url, pu_data, accept_gzip=accept_gzip, gzip_body=gzip_body)
    if status not in [200, 202]:
        raise RequestException(status, data)
    return status, data

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
    if cfg["servers"]:
        remote_server = cfg["servers"][0]
    else:
        remote_server = ("127.0.0.1", "443", "/splice/api/v1/productusage/")
    host = remote_server[0]
    port = remote_server[1]
    url = remote_server[2]

    status, data = upload_product_usage_data(host, port, url, [pu])
    print "---\n\n"
    print "Response:\n Status Code: %s\n%s" % (status, data)
