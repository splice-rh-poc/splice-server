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

from splice.common import config, splice_server_client
from splice.common.exceptions import RequestException
from splice.common.models import ProductUsage, ProductUsageTransferInfo
from logging import getLogger
_LOG = getLogger(__name__)

def upload_product_usage_data(cfg=None):
    """

    @param cfg: optional argument to use a special instance of ConfigParser to determine values,
                mainly used for unit testing,
    @return: None
    """
    cfg_info = config.get_reporting_config_info(cfg)
    if not cfg_info["servers"]:
        _LOG.info("No servers are configured to upload product usage data to")
        return
    limit = None
    if cfg_info["limit_per_call"]:
        limit = cfg_info["limit_per_call"]
    for server in cfg_info["servers"]:
        (addr, port, url) = server
        _process_product_usage_upload(addr, port, url, limit)

###
# - Internal functions below
###
def _process_product_usage_upload(addr, port, url, limit, since=None):
    """
    @param addr: address of remote server
    @param port:  port of remote server
    @param url:  url of remote server
    @param limit: max amount of objects to process per request
    @param since: Optional, date we want to send data from, intended for unit tests only
    @return: True on success, False on failure
    """
    cursor = _get_product_usage_data(addr, limit, since)
    pu_data = list(cursor)
    if not pu_data:
        return True
    last_timestamp = pu_data[-1].date
    try:
        splice_server_client.upload_product_usage_data(addr, port, url, pu_data)
    except RequestException, e:
        _LOG.exception("Received exception attempting to send %s records from %s to %s:%s\%s" % (len(pu_data), last_timestamp, addr, port, url))
        return False
    _update_last_timestamp(addr, last_timestamp)
    return True

def _update_last_timestamp(addr, timestamp):
    prod_usage_transfer = ProductUsageTransferInfo.objects(server_hostname=addr).first()
    if not prod_usage_transfer:
        prod_usage_transfer = ProductUsageTransferInfo(server_hostname=addr)
    prod_usage_transfer.last_timestamp = timestamp
    prod_usage_transfer.save()

def _get_product_usage_data(addr, limit, since=None):
    """
    Returns product usage data which has not yet been uploaded to 'addr'
    @param addr: remote server to upload data to
    @param limit: max amount of objects to process per request
    @param since: Optional, date we want to send data from, intended for unit tests only
    @type since: datetime.datetime
    @return:
    """
    last_timestamp = since
    prod_usage_transfer = ProductUsageTransferInfo.objects(server_hostname=addr).first()
    # Get the last timestamp we sent to 'addr'
    if not last_timestamp and prod_usage_transfer:
        last_timestamp = prod_usage_transfer.last_timestamp
    if last_timestamp:
        prod_usage_data = ProductUsage.objects(date__gt=last_timestamp)
    else:
        prod_usage_data = ProductUsage.objects()
    if limit:
        prod_usage_data = prod_usage_data.order_by("date").limit(limit)
    return prod_usage_data



