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

import ConfigParser
import logging
import os

from datetime import datetime
from dateutil.tz import tzutc
from mongoengine.queryset import OperationError
from StringIO import StringIO

from splice.common import config
from splice.common.exceptions import BadConfigurationException
from splice.common.models import ProductUsage

# Unit test imports
from base import BaseEntitlementTestCase

LOG = logging.getLogger(__name__)


class ProductUsageTest(BaseEntitlementTestCase):
    def setUp(self):
        super(ProductUsageTest, self).setUp()

    def tearDown(self):
        super(ProductUsageTest, self).tearDown()

    def create_config_parser(self, servers):
        raw_config_data = """
[reporting]
servers = %s
[tasks]
upload_product_usage_interval_minutes = 720
upload_product_usage_limit_per_call = 5000
        """ % (servers)
        parser = ConfigParser.SafeConfigParser()
        parser.readfp(StringIO(raw_config_data))
        return parser

    def create_product_usage(self, consumer, splice_server, instance_identifier, date=None,
                             allowed_product_info=None, unallowed_product_info=None, facts=None):
        if not date:
            date = datetime.now(tzutc())
        if not allowed_product_info:
            allowed_product_info = ["1", "2", "3"]
        if not unallowed_product_info:
            unallowed_product_info = []
        if not facts:
            facts = {"tbd": "values"}

        pu = ProductUsage()
        pu.consumer = consumer
        pu.splice_server = splice_server
        pu.date = date
        pu.instance_identifier = instance_identifier
        pu.allowed_product_info = allowed_product_info
        pu.unallowed_product_info = unallowed_product_info
        pu.facts = facts
        return pu

    def test_create_simple_product_usage(self):
        self.assertEquals(len(ProductUsage.objects()), 0)
        consumer = "consumer_uuid"
        splice_server = "splice_server_uuid"
        inst_id = "mac_addr"
        date = datetime.now(tzutc())
        pu = self.create_product_usage(consumer, splice_server, inst_id, date)
        pu.save()
        self.assertEquals(len(ProductUsage.objects()), 1)

    def test_duplicate_product_usage_not_allowed(self):
        self.assertEquals(len(ProductUsage.objects()), 0)
        consumer = "consumer_uuid"
        splice_server = "splice_server_uuid"
        inst_id = "mac_addr"
        date = datetime.now(tzutc())
        pu_a = self.create_product_usage(consumer, splice_server, inst_id, date)
        pu_a.save()
        self.assertEquals(len(ProductUsage.objects()), 1)

        caught = False
        pu_b = self.create_product_usage(consumer, splice_server, inst_id, date)
        try:
            pu_b.save()
        except OperationError, e:
            caught = True
        self.assertTrue(caught)
        self.assertEquals(len(ProductUsage.objects()), 1)

    def test_uploading_simple_product_usage(self):
        consumer = "consumer_uuid"
        splice_server = "splice_server_uuid"
        inst_id = "mac_addr"
        date = datetime.now(tzutc())
        allowed_product_info = ["1", "2", "3"]
        unallowed_product_info = ["0"]
        facts = {"tbd": "values"}
        pu_a = self.create_product_usage(consumer, splice_server, inst_id, date,
            allowed_product_info=allowed_product_info, unallowed_product_info=unallowed_product_info, facts=facts)
        self.assertEquals(len(ProductUsage.objects()), 0)

        post_data = [pu_a._data]
        LOG.info("Calling api for productusage import with post data: '%s'" % (post_data))
        resp = self.api_client.post('/api/v1/productusage/', format='json', data=post_data,
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        LOG.info("Response for productusage import: Status Code: %s, Response: %s" % (resp.status_code, resp))
        self.assertEquals(resp.status_code, 202)
        # Now check that the server api saved the object as expected
        found = ProductUsage.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].consumer, consumer)
        self.assertEquals(found[0].splice_server, splice_server)
        self.assertEquals(found[0].instance_identifier, inst_id)
        self.assertEquals(found[0].date.year, date.year)
        self.assertEquals(found[0].date.month, date.month)
        self.assertEquals(found[0].date.day, date.day)
        # TODO:  Fix timezone issue, we are doing something wrong and not handling timezones correctly
        # self.assertEquals(found[0].date.hour, date.hour)
        self.assertEquals(found[0].date.minute, date.minute)
        self.assertEquals(found[0].date.second, date.second)
        self.assertEquals(found[0].allowed_product_info, allowed_product_info)
        self.assertEquals(found[0].unallowed_product_info, unallowed_product_info)
        self.assertEquals(found[0].facts, facts)

    def test_uploading_duplicate_product_usage(self):
        consumer = "consumer_uuid"
        splice_server = "splice_server_uuid"
        inst_id = "mac_addr"
        date = datetime.now(tzutc())
        allowed_product_info = ["1", "2", "3"]
        unallowed_product_info = ["0"]
        facts = {"tbd": "values"}
        pu_a = self.create_product_usage(consumer, splice_server, inst_id, date,
            allowed_product_info=allowed_product_info, unallowed_product_info=unallowed_product_info, facts=facts)
        pu_b = self.create_product_usage(consumer, splice_server, inst_id, date,
            allowed_product_info=allowed_product_info, unallowed_product_info=unallowed_product_info, facts=facts)
        self.assertEquals(len(ProductUsage.objects()), 0)

        post_data = [pu_a._data, pu_b._data]
        LOG.info("Calling api for productusage import with post data: '%s'" % (post_data))
        resp = self.api_client.post('/api/v1/productusage/', format='json', data=post_data,
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        LOG.info("Response for productusage import: Status Code: %s, Response: %s" % (resp.status_code, resp))
        self.assertEquals(resp.status_code, 409)
        # Now check that the server api saved the object as expected
        found = ProductUsage.objects()
        found = ProductUsage.objects()
        self.assertEquals(len(found), 1)

    def test_uploading_multiple_product_usages(self):
        consumer = "consumer_uuid"
        splice_server = "splice_server_uuid"
        date = datetime.now(tzutc())
        allowed_product_info = ["1", "2", "3"]
        unallowed_product_info = ["0"]
        facts = {"tbd": "values"}
        pu_a = self.create_product_usage(consumer, splice_server, "instance_a", date,
            allowed_product_info=allowed_product_info, unallowed_product_info=unallowed_product_info, facts=facts)
        pu_b = self.create_product_usage(consumer, splice_server, "instance_b", date,
            allowed_product_info=allowed_product_info, unallowed_product_info=unallowed_product_info, facts=facts)
        self.assertEquals(len(ProductUsage.objects()), 0)

        post_data = [pu_a._data, pu_b._data]
        LOG.info("Calling api for productusage import with post data: '%s'" % (post_data))
        resp = self.api_client.post('/api/v1/productusage/', format='json', data=post_data,
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        LOG.info("Response for productusage import: Status Code: %s, Response: %s" % (resp.status_code, resp))
        self.assertEquals(resp.status_code, 202)
        # Now check that the server api saved the object as expected
        found = ProductUsage.objects()
        self.assertEquals(len(found), 2)

    def test_config_single_endpoint(self):
        servers = "255.255.255.255:443:/splice/api/v1/productusage"
        parser = self.create_config_parser(servers)
        data = config.get_reporting_config_info(cfg=parser)
        self.assertTrue(data.has_key("servers"))
        self.assertEquals(len(data["servers"]), 1)
        self.assertEquals(data["servers"][0][0], "255.255.255.255")
        self.assertEquals(data["servers"][0][1], 443)
        self.assertEquals(data["servers"][0][2], "/splice/api/v1/productusage")

    def test_config_multiple_endpoints(self):
        # Test config parsing with bad values
        servers = "255.255.255.255:443:/splice/api/v1/productusage, 192.168.1.1:443:/splice/api/v1/productusage, test.example.com:443:/api/v1/productusage"
        parser = self.create_config_parser(servers)
        data = config.get_reporting_config_info(cfg=parser)
        self.assertTrue(data.has_key("servers"))
        self.assertEquals(len(data["servers"]), 3)
        self.assertEquals(data["servers"][0][0], "255.255.255.255")
        self.assertEquals(data["servers"][0][1], 443)
        self.assertEquals(data["servers"][0][2], "/splice/api/v1/productusage")

        self.assertEquals(data["servers"][1][0], "192.168.1.1")
        self.assertEquals(data["servers"][1][1], 443)
        self.assertEquals(data["servers"][1][2], "/splice/api/v1/productusage")

        self.assertEquals(data["servers"][2][0], "test.example.com")
        self.assertEquals(data["servers"][2][1], 443)
        self.assertEquals(data["servers"][2][2], "/api/v1/productusage")

    def test_config_bad_data(self):
        raw_config_data = """
[reporting]
servers = 255.255.255.255:/splice/api/v1/productusage 192.168.1.1:443:/splice/api/v1/productusage, test.example.com:443:/api/v1/productusage
        """
        parser = ConfigParser.SafeConfigParser()
        parser.readfp(StringIO(raw_config_data))
        caught = False
        try:
            data = config.get_reporting_config_info(cfg=parser)
        except BadConfigurationException, e:
            caught = True
        self.assertTrue(caught)