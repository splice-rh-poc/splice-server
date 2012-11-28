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



# Responsible for making a remote call to rhic_serve to fetch data for RHIC to Product mapping
#
import gzip
import httplib
import json
import logging
import time
import urllib
import StringIO

from django.conf import settings

from splice.common import config
from splice.common.connect import BaseConnection
from splice.common.exceptions import RequestException


_LOG = logging.getLogger(__name__)

def get_connection(host, port, cert, key, accept_gzip=False):
    # Note: this method will be mocked out in unit tests
    return BaseConnection(host, port, handler="", https=True, cert_file=cert, key_file=key, accept_gzip=accept_gzip)

def _form_url(url, last_sync=None, offset=None, limit=None):
    query_params = {}
    if last_sync:
        query_params["modified_date__gt"] = last_sync,
    if offset is not None:
        query_params["offset"] = offset
    if limit is not None:
        query_params["limit"] = limit
    if query_params:
        data = urllib.urlencode(query_params, True)
        url = url +"?" + data
    return url

def get_single_rhic(host, port, url, uuid):
    cfg = config.get_rhic_serve_config_info()
    url = url + uuid + "/"
    try:
        conn = get_connection(host, port, cfg["client_cert"], cfg["client_key"])
        return conn.GET(url)
    except Exception, e:
        _LOG.exception("Caught exception from 'get_single_rhic' with config info: %s"  % (cfg))
        raise

def get_all_rhics(host, port, url, last_sync=None, offset=None, limit=None, accept_gzip=True):
    cfg = config.get_rhic_serve_config_info()
    try:
        conn = get_connection(host, port, cfg["client_cert"], cfg["client_key"], accept_gzip=accept_gzip)
        url_with_params = _form_url(url, last_sync, offset, limit)
        status, data = conn.GET(url_with_params)
        if status == 200:
            return data["objects"], data["meta"]
        raise RequestException(status, data)
    except Exception, e:
        _LOG.exception("Caught exception from 'get_all_rhics' with config info: %s" % (cfg))
        raise

if __name__ == "__main__":
    from datetime import timedelta
    from datetime import datetime
    from dateutil.tz import tzutc
    last_sync = datetime.now(tzutc()) - timedelta(days=30)
    config.init(settings.SPLICE_CONFIG_FILE)
    cfg = config.get_rhic_serve_config_info()
    data, meta = get_all_rhics(host=cfg["host"], port=cfg["port"], url=cfg["rhics_url"],
        offset=0, limit=1000,
        last_sync=last_sync, accept_gzip=True)
    print "--- Test Sync all RHICs ---"
    print data
    if len(data) > 0:
        uuid = data[0]["uuid"]
        print "\n---Test A Single RHIC ---\n"
        print get_single_rhic(host=cfg["host"], port=cfg["port"], url=cfg["rhics_url"], uuid=uuid)
    print "\n -- Test an unknown RHIC ---\n"
    uuid = "1a1aa1aa-f6f4-45be-9d86-deb97a79d181"
    print get_single_rhic(host=cfg["host"], port=cfg["port"], url=cfg["rhics_url"], uuid=uuid)
