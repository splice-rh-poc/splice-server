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

import datetime
import json
import logging

from splice.common import utils
from splice.common.models import Pool

# Unit test imports
from base import BaseEntitlementTestCase

LOG = logging.getLogger(__name__)


class PoolTest(BaseEntitlementTestCase):
    def setUp(self):
        super(PoolTest, self).setUp()

    def tearDown(self):
        super(PoolTest, self).tearDown()

    def test_date_as_string_is_converted_on_save(self):
        found = Pool.objects()
        self.assertEquals(len(found), 0)

        datestr = "2012-12-06T11:13:06.432367"
        p = Pool()
        p.uuid = "a"
        p.account = 1
        p.active = True
        p.contract = 1
        p.product_id = "something"
        p.product_name = "something_name"
        p.product_attributes = {}
        p.provided_products = []
        p.created = datestr
        p.start_date = datestr
        p.end_date = datestr
        p.updated = datestr
        p.quantity = 0
        p.save()

        found = Pool.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, p.uuid)
        self.assertEquals(found[0].account, p.account)
        self.assertEquals(found[0].active, p.active)
        self.assertEquals(found[0].contract, p.contract)
        self.assertEquals(found[0].product_id, p.product_id)
        self.assertEquals(found[0].product_name, p.product_name)
        self.assertEquals(found[0].product_attributes, p.product_attributes)
        self.assertEquals(found[0].provided_products, p.provided_products)
        self.assertEquals(found[0].quantity, p.quantity)
        self.assertEquals(type(found[0].created), datetime.datetime)
        self.assertEquals(type(found[0].updated), datetime.datetime)
        self.assertEquals(type(found[0].start_date), datetime.datetime)
        self.assertEquals(type(found[0].end_date), datetime.datetime)

    def test_get_pool_collection(self):
        datestr = "2010-10-01T11:01:00.432367"
        a = Pool(uuid="uuid a", account=1, contract=1, active=True, product_id="pid1", product_name="pname",
                 quantity=1, created=datestr, updated=datestr, start_date=datestr, end_date=datestr)
        a.save()
        b = Pool(uuid="uuid b", account=1, contract=1, active=True, product_id="pid1", product_name="pname",
                 quantity=1, created=datestr, updated=datestr, start_date=datestr, end_date=datestr)
        b.save()

        resp = self.api_client.get('/api/v1/pool/', format='json',
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        self.assertEquals(resp.status_code, 200)

    def test_example_with_raw_string_data(self):
        example = {"objects": [
            {
                "uuid": "uuid_a",
                "account": "0",
                "contract": "1",
                "active": "True",
                "product_id": "p0",
                "product_name": "p0_name",
                "quantity": "1",
                "created": "2012-12-07T15:35:54.448000",
                "updated": "2012-12-07T15:35:54.448000",
                "start_date": "2012-12-07T15:35:54.448000",
                "end_date": "2012-12-07T15:35:54.448000",
            },
            {
                "uuid": "uuid_b",
                "account": "0",
                "contract": "1",
                "active": "True",
                "product_id": "p0",
                "product_name": "p0_name",
                "quantity": "1",
                "created": "2012-12-07T15:35:54.448000",
                "updated": "2012-12-07T15:35:54.448000",
                "start_date": "2012-12-07T15:35:54.448000",
                "end_date": "2012-12-07T15:35:54.448000",
            },
        ]}
        post_data = json.dumps(example)
        LOG.info("Post to pool with data: %s" % (post_data))
        resp = self.raw_api_client.post('/api/v1/pool/', format='json', data=post_data,
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        LOG.info("Response: %s" % (resp))
        self.assertEquals(resp.status_code, 204)
        found = Pool.objects()
        self.assertEquals(len(found), 2)
        self.assertIn(found[0].uuid, ("uuid_a", "uuid_b"))

    def test_uploading_single_pool(self):
        found = Pool.objects()
        self.assertEquals(len(found), 0)

        datestr = "2012-12-06T11:13:06.432367+00:00"
        p = Pool()
        p.uuid = "a"
        p.account = 1
        p.active = True
        p.contract = 1
        p.product_id = "something"
        p.product_name = "something_name"
        p.product_attributes = {}
        p.provided_products = []
        p.created = datestr
        p.start_date = datestr
        p.end_date = datestr
        p.updated = datestr
        p.quantity = 0

        example = {"objects":[p]}
        post_data = utils.obj_to_json(example)
        LOG.info("Calling api for pool import with post data: '%s'" % (post_data))
        resp = self.raw_api_client.post('/api/v1/pool/', format='json', data=post_data,
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        self.assertEquals(resp.status_code, 204)
        # Now check that the server api saved the object as expected
        found = Pool.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, p.uuid)
        self.assertEquals(found[0].account, p.account)
        self.assertEquals(found[0].active, p.active)
        self.assertEquals(found[0].contract, p.contract)
        self.assertEquals(found[0].product_id, p.product_id)
        self.assertEquals(found[0].product_name, p.product_name)
        self.assertEquals(found[0].product_attributes, p.product_attributes)
        self.assertEquals(found[0].provided_products, p.provided_products)
        self.assertEquals(found[0].quantity, p.quantity)
        self.assertEquals(type(found[0].created), datetime.datetime)
        self.assertEquals(str(found[0].created), "2012-12-06 11:13:06.432000+00:00")

        self.assertEquals(type(found[0].updated), datetime.datetime)
        self.assertEquals(str(found[0].updated), "2012-12-06 11:13:06.432000+00:00")

        self.assertEquals(type(found[0].start_date), datetime.datetime)
        self.assertEquals(str(found[0].start_date), "2012-12-06 11:13:06.432000+00:00")

        self.assertEquals(type(found[0].end_date), datetime.datetime)
        self.assertEquals(str(found[0].end_date), "2012-12-06 11:13:06.432000+00:00")

    def test_uploading_duplicate(self):
        #
        # Similar to test_uploading_single_pool, except for this test we will save the Pool object we create
        # then upload the same exact data and verify we have only 1 record in the DB...no duplicate should be present.
        #
        found = Pool.objects()
        self.assertEquals(len(found), 0)

        datestr = "2012-12-06T11:13:06.432367"
        p = Pool()
        p.uuid = "a"
        p.account = 1
        p.active = True
        p.contract = 1
        p.product_id = "something"
        p.product_name = "something_name"
        p.product_attributes = {}
        p.provided_products = []
        p.created = datestr
        p.start_date = datestr
        p.end_date = datestr
        p.updated = datestr
        p.quantity = 0
        p.save()

        self.assertEquals(len(found), 1)
        example = {"objects":[p]}
        post_data = utils.obj_to_json(example)
        LOG.info("Calling api for pool import with post data: '%s'" % (post_data))
        resp = self.raw_api_client.post('/api/v1/pool/', format='json', data=post_data,
                                        SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        self.assertEquals(resp.status_code, 204)
        # Now check that the server api saved the object as expected
        found = Pool.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, p.uuid)

    def test_upload_older_pool(self):
        found = Pool.objects()
        self.assertEquals(len(found), 0)
        # Create 'newer' pool and save to DB

        datestr = "2012-12-06T11:13:06.432367"
        newer = Pool()
        newer.uuid = "a"
        newer.account = 1
        newer.active = True
        newer.contract = 1
        newer.product_id = "something"
        newer.product_name = "something_name"
        newer.product_attributes = {}
        newer.provided_products = []
        newer.created = datestr
        newer.start_date = datestr
        newer.end_date = datestr
        newer.updated = datestr
        newer.quantity = 0
        newer.save()

        found = Pool.objects()
        self.assertEquals(len(found), 1)

        # Create 'older' which is one month older than newer
        older = Pool()
        older.uuid = newer.uuid
        older.account = 20
        older.contract = 400
        older.active = False
        older.product_id = "something older"
        older.product_name = "something older name"
        older.product_attributes = {}
        older.provided_products = []
        older.created = newer.created
        older.updated = "2012-11-06T11:13:06.432367" # 1 month older
        older.start_date = older.updated
        older.end_date = older.updated
        older.quantity = 1

        example = {"objects": [older._data]}
        post_data = utils.obj_to_json(example)
        LOG.info("Calling api for pool import with post data: '%s'" % (post_data))
        resp = self.raw_api_client.post('/api/v1/pool/', format='json', data=post_data,
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        LOG.info("Status Code: %s, Response: %s" % (resp.status_code, resp))
        self.assertEquals(resp.status_code, 204)
        # Now check that the server api kept the 'newer' as is and ignored the older
        found = Pool.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, newer.uuid)
        self.assertEquals(found[0].active, newer.active)
        self.assertEquals(found[0].account, newer.account)
        self.assertEquals(found[0].contract, newer.contract)
        self.assertEquals(found[0].quantity, newer.quantity)
        self.assertEquals(found[0].product_id, newer.product_id)
        self.assertEquals(found[0].product_name, newer.product_name)
        self.assertEquals(found[0].product_attributes, newer.product_attributes)
        self.assertEquals(found[0].provided_products, newer.provided_products)
        self.assertEquals(str(found[0].created), "2012-12-06 11:13:06.432000+00:00")
        self.assertEquals(str(found[0].updated), "2012-12-06 11:13:06.432000+00:00")
        self.assertEquals(str(found[0].start_date), "2012-12-06 11:13:06.432000+00:00")
        self.assertEquals(str(found[0].end_date), "2012-12-06 11:13:06.432000+00:00")

    def test_upload_newer_spliceserver(self):
        found = Pool.objects()
        self.assertEquals(len(found), 0)
        # Create 'older' pool and save to DB
        older = Pool()
        older.uuid = "a"
        older.account = 20
        older.contract = 400
        older.active = False
        older.product_id = "something older"
        older.product_name = "something older name"
        older.product_attributes = {}
        older.provided_products = []
        older.created = "2012-11-06T11:13:06.432367+00:00"
        older.updated = "2012-11-06T11:13:06.432367+00:00" # 1 month older
        older.start_date = older.updated
        older.end_date = older.updated
        older.quantity = 1
        older.save()
        found = Pool.objects()
        self.assertEquals(len(found), 1)

        datestr = "2012-12-06T11:13:06.432367+00:00"
        newer = Pool()
        newer.uuid = older.uuid
        newer.account = 1
        newer.active = True
        newer.contract = 1
        newer.product_id = "something"
        newer.product_name = "something_name"
        newer.product_attributes = {}
        newer.provided_products = []
        newer.created = datestr
        newer.start_date = datestr
        newer.end_date = datestr
        newer.updated = datestr
        newer.quantity = 0

        example = {"objects": [newer]}
        post_data = utils.obj_to_json(example)
        LOG.info("Calling api for pool with post data: '%s'" % (post_data))
        resp = self.raw_api_client.post('/api/v1/pool/', format='json', data=post_data,
                                        SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        LOG.info("Status Code: %s, Response: %s" % (resp.status_code, resp))
        self.assertEquals(resp.status_code, 204)
        # Now check that the server api kept the 'newer' as is and ignored the older
        found = Pool.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, newer.uuid)
        self.assertEquals(found[0].active, newer.active)
        self.assertEquals(found[0].account, newer.account)
        self.assertEquals(found[0].contract, newer.contract)
        self.assertEquals(found[0].quantity, newer.quantity)
        self.assertEquals(found[0].product_id, newer.product_id)
        self.assertEquals(found[0].product_name, newer.product_name)
        self.assertEquals(found[0].product_attributes, newer.product_attributes)
        self.assertEquals(found[0].provided_products, newer.provided_products)
        self.assertEquals(str(found[0].created), "2012-12-06 11:13:06.432000+00:00")
        self.assertEquals(str(found[0].updated), "2012-12-06 11:13:06.432000+00:00")
        self.assertEquals(str(found[0].start_date), "2012-12-06 11:13:06.432000+00:00")
        self.assertEquals(str(found[0].end_date), "2012-12-06 11:13:06.432000+00:00")
