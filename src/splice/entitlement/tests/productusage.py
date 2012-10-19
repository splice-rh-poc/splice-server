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

from datetime import datetime
from dateutil.tz import tzutc
import logging
from mongoengine.queryset import OperationError

from splice.common.models import ProductUsage

# Unit test imports
from base import BaseEntitlementTestCase

LOG = logging.getLogger(__name__)


class ProductUsageTest(BaseEntitlementTestCase):
    def setUp(self):
        super(ProductUsageTest, self).setUp()

    def tearDown(self):
        super(ProductUsageTest, self).tearDown()

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
        resp = self.api_client.post('/api/v1/productusage/', format='json', data=post_data)
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
        resp = self.api_client.post('/api/v1/productusage/', format='json', data=post_data)
        LOG.info("Response for productusage import: Status Code: %s, Response: %s" % (resp.status_code, resp))
        self.assertEquals(resp.status_code, 202)
        # Now check that the server api saved the object as expected
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
        resp = self.api_client.post('/api/v1/productusage/', format='json', data=post_data)
        LOG.info("Response for productusage import: Status Code: %s, Response: %s" % (resp.status_code, resp))
        self.assertEquals(resp.status_code, 202)
        # Now check that the server api saved the object as expected
        found = ProductUsage.objects()
        self.assertEquals(len(found), 2)

