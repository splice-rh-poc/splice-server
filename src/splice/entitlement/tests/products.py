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
from splice.common.models import Product

# Unit test imports
from base import BaseEntitlementTestCase

LOG = logging.getLogger(__name__)


class ProductTest(BaseEntitlementTestCase):
    def setUp(self):
        super(ProductTest, self).setUp()

    def tearDown(self):
        super(ProductTest, self).tearDown()

    def test_date_as_string_is_converted_on_save(self):
        found = Product.objects()
        self.assertEquals(len(found), 0)

        p = Product()
        p.product_id = "pid"
        p.name = "pname"
        p.engineering_ids = ["3", "5"]
        p.created = "2012-12-06T11:13:06.432367+00:00"
        p.updated = "2012-12-06T11:13:06.432367+00:00"
        p.eng_prods = []
        p.attrs = {}
        p.dependent_product_ids = []
        p.save()

        found = Product.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].product_id, p.product_id)
        self.assertEquals(found[0].name, p.name)
        self.assertEquals(found[0].engineering_ids, p.engineering_ids)
        self.assertEquals(found[0].eng_prods, p.eng_prods)
        self.assertEquals(found[0].attrs, p.attrs)
        self.assertEquals(found[0].dependent_product_ids, p.dependent_product_ids)
        self.assertIsNotNone(found[0].created)
        self.assertEquals(type(found[0].created), datetime.datetime)
        self.assertIsNotNone(found[0].updated)
        self.assertEquals(type(found[0].updated), datetime.datetime)
        self.assertEquals(str(found[0].created), "2012-12-06 11:13:06.432000+00:00")
        self.assertEquals(str(found[0].updated), "2012-12-06 11:13:06.432000+00:00")

    def test_get_product_collection(self):
        a = Product(product_id="a", name="namea", engineering_ids=["1"], eng_prods=[],
                    attrs={}, dependent_product_ids=[],
                    created="2012-12-06T11:13:06.432367+00:00",
                    updated="2012-12-06T11:13:06.432367+00:00")
        a.save()
        b = Product(product_id="b", name="nameb", engineering_ids=["1"], eng_prods=[],
                    attrs={}, dependent_product_ids=[],
                    created="2012-12-06T11:13:06.432367+00:00",
                    updated="2012-12-06T11:13:06.432367+00:00")
        b.save()
        resp = self.api_client.get('/api/v1/product/', format='json',
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        self.assertEquals(resp.status_code, 200)
        LOG.info("Status Code: %s, Response: %s" % (resp.status_code, resp))
        found = Product.objects()
        self.assertEquals(len(found), 2)

    def test_example_with_raw_string_data(self):
        example = {"objects": [
            {
                "product_id": "a",
                "name": "prod_name_a",
                "engineering_ids": ["1"],
                "eng_prods": [],
                "attrs": {},
                "created": "2012-12-07T15:35:54.448000",
                "updated": "2012-12-07T15:35:54.448000",
            },
            {
                "product_id": "b",
                "name": "prod_name_b",
                "engineering_ids": ["3"],
                "eng_prods": [],
                "attrs": {},
                "created": "2012-12-07T15:35:54.448000",
                "updated": "2012-12-07T15:35:54.448000",
            },

        ]}
        post_data = json.dumps(example)
        resp = self.raw_api_client.post('/api/v1/product/', format='json', data=post_data,
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        self.assertEquals(resp.status_code, 204)
        found = Product.objects()
        self.assertEquals(len(found), 2)
        self.assertIn(found[0].product_id, ("a", "b"))

    def test_uploading_single_product(self):
        found = Product.objects()
        self.assertEquals(len(found), 0)

        p = Product()
        p.product_id = "a"
        p.name = "a_name"
        p.engineering_ids = ["1"]
        p.eng_prods = []
        p.attrs = {}
        p.created = "2012-12-07T15:35:54.448000"
        p.updated = "2012-12-07T15:35:54.448000"

        example = {"objects":[p]}
        post_data = utils.obj_to_json(example)
        LOG.info("Calling api for product import with post data: '%s'" % (post_data))
        resp = self.raw_api_client.post('/api/v1/product/', format='json', data=post_data,
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        LOG.info("Status Code: %s, Response: %s" % (resp.status_code, resp))
        self.assertEquals(resp.status_code, 204)
        # Now check that the server api saved the object as expected
        found = Product.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].product_id, p.product_id)
        self.assertEquals(found[0].name, p.name)
        self.assertEquals(found[0].engineering_ids, p.engineering_ids)
        self.assertEquals(found[0].eng_prods, p.eng_prods)
        self.assertIsNotNone(found[0].created)
        self.assertEquals(str(found[0].created), '2012-12-07 15:35:54.448000+00:00')
        self.assertIsNotNone(found[0].updated)
        self.assertEquals(str(found[0].updated), '2012-12-07 15:35:54.448000+00:00')

    def test_uploading_duplicate(self):
        found = Product.objects()
        self.assertEquals(len(found), 0)

        p = Product()
        p.product_id = "a"
        p.name = "a_name"
        p.engineering_ids = ["1"]
        p.eng_prods = []
        p.attrs = {}
        p.created = "2012-12-07T15:35:54.448000"
        p.updated = "2012-12-07T15:35:54.448000"
        p.save()  # <- This is the big difference from test_uploading_single_product

        example = {"objects":[p]}
        post_data = utils.obj_to_json(example)
        LOG.info("Calling api for product import with post data: '%s'" % (post_data))
        resp = self.raw_api_client.post('/api/v1/product/', format='json', data=post_data,
                                        SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        LOG.info("Status Code: %s, Response: %s" % (resp.status_code, resp))
        self.assertEquals(resp.status_code, 204)
        # Now check that the server api saved the object as expected
        found = Product.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].product_id, p.product_id)

    def test_upload_older_product(self):
        found = Product.objects()
        self.assertEquals(len(found), 0)
        # Create 'newer' product and save to DB

        newer = Product()
        newer.product_id = "a"
        newer.name = "a_name"
        newer.engineering_ids = ["1"]
        newer.eng_prods = []
        newer.attrs = {}
        newer.created = "2012-12-07T15:35:54.448000"
        newer.updated = "2012-12-07T15:35:54.448000"
        newer.save()  # <- This is the big difference from test_uploading_single_product
        found = Product.objects()
        self.assertEquals(len(found), 1)

        # Create 'older' which is one month older than newer
        older = Product()
        older.product_id = "a"
        older.name = "old name"
        older.engineering_ids = ["old1"]
        older.eng_prods = [{"more old info": 1}]
        older.attrs = {"old": "info"}
        older.created = "2012-10-01T01:01:01.111111"
        older.updated = "2012-10-01T01:01:01.111111"

        example = {"objects": [older]}
        post_data = utils.obj_to_json(example)
        LOG.info("Calling api for product import with post data: '%s'" % (post_data))
        resp = self.raw_api_client.post('/api/v1/product/', format='json', data=post_data,
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        LOG.info("Status Code: %s, Response: %s" % (resp.status_code, resp))
        self.assertEquals(resp.status_code, 204)
        # Now check that the server api kept the 'newer' as is and ignored the older
        found = Product.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].product_id, newer.product_id)
        self.assertEquals(found[0].name, newer.name)
        self.assertEquals(found[0].engineering_ids, newer.engineering_ids)
        self.assertEquals(found[0].eng_prods, newer.eng_prods)
        self.assertEquals(str(found[0].updated), '2012-12-07 15:35:54.448000+00:00')

    def test_upload_newer_product(self):
        found = Product.objects()
        self.assertEquals(len(found), 0)
        # Create 'older' which is one month older than newer
        older = Product()
        older.product_id = "a"
        older.name = "old name"
        older.engineering_ids = ["old1"]
        older.eng_prods = [{"more old info": 1}]
        older.attrs = {"old": "info"}
        older.created = "2012-10-01T01:01:01.111111"
        older.updated = "2012-10-01T01:01:01.111111"
        older.save()
        found = Product.objects()
        self.assertEquals(len(found), 1)

        newer = Product()
        newer.product_id = "a"
        newer.name = "a_name"
        newer.engineering_ids = ["1"]
        newer.eng_prods = [{"new_info": 5}]
        newer.attrs = {}
        newer.created = "2012-12-07T15:35:54.448000"
        newer.updated = "2012-12-07T15:35:54.448000"

        example = {"objects":[newer]}
        post_data = utils.obj_to_json(example)
        LOG.info("Calling api for product import with post data: '%s'" % (post_data))
        resp = self.raw_api_client.post('/api/v1/product/', format='json', data=post_data,
                                        SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        LOG.info("Status Code: %s, Response: %s" % (resp.status_code, resp))
        self.assertEquals(resp.status_code, 204)
        # Now check that the server api saved the object as expected
        found = Product.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].product_id, newer.product_id)
        self.assertEquals(found[0].name, newer.name)
        self.assertEquals(found[0].engineering_ids, newer.engineering_ids)
        self.assertEquals(found[0].eng_prods, newer.eng_prods)
        self.assertIsNotNone(found[0].created)
        self.assertEquals(str(found[0].created), '2012-12-07 15:35:54.448000+00:00')
        self.assertIsNotNone(found[0].updated)
        self.assertEquals(str(found[0].updated), '2012-12-07 15:35:54.448000+00:00')

