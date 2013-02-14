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

import logging
import urllib

from splice.common.connect import BaseConnection
from splice.common.exceptions import RequestException

_LOG = logging.getLogger(__name__)


def get_connection(host, port, username, password, https=False):
    # Note: this method will be mocked out in unit tests
    return BaseConnection(host, port, handler="", https=https, username=username, password=password)


def GET(host, port, username, password, https, url):
    try:
        conn = get_connection(host, port, username, password, https)
        status, data = conn.GET(url)
        if status == 200:
            return data
        raise RequestException(status, data)
    except Exception, e:
        _LOG.exception("Caught exception on %s:%s %s" % (host, port, url))
        raise


def get_subscriptions(host, port, username, password, https=False, url="/candlepin/subscriptions"):
    return GET(host, port, username, password, https, url)


def get_rules(host, port, username, password, https=False, url="/candlepin/rules/"):
    #TODO
    # - Response is a base 64 encoded string
    "Decoded String: " + decoded.decode('base64', 'strict')
    return GET(host, port, username, password, https, url)


def get_products(host, port, username, password, https=False, url="/candlepin/products"):
    return GET(host, port, username, password, https, url)


def get_pools(host, port, username, password, https=False, url="/candlepin/pools"):
    return GET(host, port, username, password, https, url)


def get_owners(host, port, username, password, https=False, url="/candlepin/owners"):
    return GET(host, port, username, password, https, url)


def get_entitlements(host, port, username, password, https=False, url="/candlepin/entitlements"):
    return GET(host, port, username, password, https, url)


def get_consumers(host, port, username, password, https=False, url="/candlepin/consumers"):
    return GET(host, port, username, password, https, url)


def get_entitlement(host, port, url, requested_products, identity,
                    username, password,
                    start_date=None, end_date=None):
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
    @return:
    @raise RequestException if a status code other than '200' or '202' is returned from remote server
    """
    try:
        conn = get_connection(host, port, username, password)
        url_with_params = _form_url(url, requested_products, identity, start_date, end_date)
        status, data = conn.GET(url_with_params)
        if status == 200:
            return parse_data(data)
        raise RequestException(status, data)
    except Exception, e:
        _LOG.exception("Caught exception trying to request ent cert from %s:%s/%s for identity %s with products %s" % \
            (host, port, url, identity, requested_products))
        raise

def _form_url(url, requested_products, identity, start_date=None, end_date=None):
    query_params = {
        "product": requested_products,
        }
    data = urllib.urlencode(query_params, True)
    if url[-1] != "/":
        url += "/"
    url += identity + "?" + data
    if start_date and end_date:
        url += "&start=%s&end=%s" % (urllib.quote_plus(start_date),
                                     urllib.quote_plus(end_date))
    return url

def parse_data(data):
    certs = []
    for d in data["certificates"]:
        item = (d["cert"], d["key"], d["serial"]["serial"])
        certs.append(item)
    return certs

if __name__ == "__main__":
    import datetime
    import pytz
    from django.conf import settings
    from splice.common import config

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
        end_date=end_date.isoformat())
    print "---\n\n"
    print "certs = \n%s" % (certs)
