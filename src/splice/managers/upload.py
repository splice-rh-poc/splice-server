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

import time

from splice.common import config, splice_server_client
from splice.common.exceptions import RequestException
from splice.common.models import ProductUsage, SpliceServer, SpliceServerTransferInfo
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
        try:
            (addr, port, url) = server
            _process_product_usage_upload(addr, port, url, limit)
            _process_splice_server_metadata_upload(addr, port, url)
        except Exception, e:
            _LOG.exception("Caught exception when processing upload to (%s, %s, %s)" % (addr, port, url))
            _LOG.info("Related configuration is: '%s'" % (cfg_info))
###
# - Internal functions below
###
def _process_splice_server_metadata_upload(addr, port, url, since=None):
    url = url + "/spliceserver/" # must end in '/'
    cursor = _get_splice_server_metadata(addr, since)
    data = list(cursor)
    if not data:
        _LOG.info("No new splice server data to upload")
        return True
    last_timestamp = data[-1].modified
    try:
        _LOG.info("Uploading %s SpliceServer objects to %s:%s/%s" % (len(data), addr, port, url))
        splice_server_client.upload_splice_server_metadata(addr, port, url, data)
    except RequestException, e:
        _LOG.exception("Received exception attempting to send %s records from %s to %s:%s\%s" % (len(data), last_timestamp, addr, port, url))
        return False
    _update_last_timestamp(addr, last_timestamp, SpliceServerTransferInfo)
    return True

def _process_product_usage_upload(addr, port, url, limit):
    """
    @param addr: address of remote server
    @param port:  port of remote server
    @param url:  url of remote server
    @param limit: max amount of objects to process per request
    @return: True on success, False on failure
    """
    url = url + "/productusage/"  #must end in '/'
    time_a = time.time()
    cursor = _get_product_usage_data(addr, limit)
    time_b = time.time()
    pu_data = list(cursor)
    time_c = time.time()
    if not pu_data:
        _LOG.info("No new product usage data to upload")
        return True
    #last_timestamp = pu_data[-1].date
    try:
        _LOG.info("Uploading %s ProductUsage entries to %s:%s/%s" % (len(pu_data), addr, port, url))
        # TODO:
        #  Examine return values and determine, what/if any objects were not successfuly uploaded.
        time_d = time.time()
        splice_server_client.upload_product_usage_data(addr, port, url, pu_data)
        time_e = time.time()
        #  Mark the successfully uploaded objects as transferred
        #  TODO:  Update logic to account for return value from upload call
        object_ids = [x.id for x in pu_data]
        for oid in object_ids:
            ProductUsage.objects(id=oid).update(add_to_set__tracker=addr)
        time_f = time.time()
        _LOG.info("%s seconds to fetch/upload %s ProductUsage entries to %s:%s/%s" % (time_f-time_a, len(pu_data), addr, port, url))
        _LOG.info("  %s seconds to fetch %s ProductUsage entries, %s for initial mongo query %s seconds to convert to list" % \
                  (time_c-time_a, len(pu_data), time_b-time_a, time_c-time_b))
        _LOG.info("  %s seconds to upload %s ProductUsage entries, %s seconds to update tracker" % (time_e-time_d, len(pu_data), time_f-time_e))
        #  Log items unsuccessful and retry upload
    except RequestException, e:
        #_LOG.exception("Received exception attempting to send %s records from %s to %s:%s\%s" % (len(pu_data), last_timestamp, addr, port, url))
        _LOG.exception("Received exception attempting to send %s records from %s to %s:%s\%s" % (len(pu_data), addr, port, url))
        return False
    #_update_last_timestamp(addr, last_timestamp, ProductUsageTransferInfo)
    return True

def _update_last_timestamp(addr, timestamp, transfer_cls):
    transfer = transfer_cls.objects(server_hostname=addr).first()
    if not transfer:
        transfer = transfer_cls(server_hostname=addr)
    transfer.last_timestamp = timestamp
    transfer.save()

def _get_splice_server_metadata(addr, since=None):
    """
    Returns splice server metadata which has not yet been uploaded to 'addr'
    @param addr: remote server to upload data to
    @param since: Optional, date we want to send data from, intended for unit tests only
    @type since: datetime.datetime
    @return: list of splice server objects ordered by date
    """
    last_timestamp = since
    data_transfer = SpliceServerTransferInfo.objects(server_hostname=addr).first()
    # Get the last timestamp we sent to 'addr'
    if not last_timestamp and data_transfer:
        last_timestamp = data_transfer.last_timestamp
    if last_timestamp:
        data = SpliceServer.objects(modified__gt=last_timestamp)
    else:
        data = SpliceServer.objects()
    data = data.order_by("modified")
    _LOG.info("Retrieved %s items to send to %s, since last timestamp of %s" % (len(data), addr, last_timestamp))
    return data

def _get_product_usage_data(addr, limit):
    """
    Returns product usage data which has not yet been uploaded to 'addr'
    @param addr: remote server to upload data to
    @param limit: max amount of objects to process per request
    @return: list of product usage objects ordered by date
    """
    #TODO:
    #  - Modify query to not fetch the "tracker" field this way it is always blank
    prod_usage_data = ProductUsage.objects(tracker__nin=[addr])
    prod_usage_data = prod_usage_data.order_by("date")

    if limit:
        prod_usage_data = prod_usage_data.limit(limit)
    # Keep 'tracker' information private to this server
    for pu in prod_usage_data:
        pu.tracker = [] #
    _LOG.info("Retrieved %s items to send to %s" % (len(prod_usage_data), addr))
    return prod_usage_data



