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

import json
import logging
import os

from splice.common import utils
from splice.common.models import Rules

# Unit test imports
from base import BaseEntitlementTestCase, TEST_DATA_DIR

LOG = logging.getLogger(__name__)


class RulesTest(BaseEntitlementTestCase):
    def setUp(self):
        super(RulesTest, self).setUp()

    def tearDown(self):
        super(RulesTest, self).tearDown()

    def test_get_rules_collection(self):
        a = Rules(version="0", data="hi")
        b = Rules(version="1", data="hello")
        a.save()
        b.save()
        resp = self.api_client.get('/api/v1/rules/', format='json',
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        self.assertEquals(resp.status_code, 200)
        LOG.info("Status Code: %s, Response: %s" % (resp.status_code, resp))

    def test_example_with_raw_string_data(self):

        example_rules_file = os.path.join(TEST_DATA_DIR, "candlepin_rules.json")
        f = open(example_rules_file, 'r')
        try:
            example_rules = f.read()
        finally:
            f.close()

        example = {"objects": [
            {
                "version": "0",
                "data": example_rules
            },
        ]}
        found = Rules.objects()
        self.assertEquals(len(found), 0)
        post_data = json.dumps(example)
        resp = self.raw_api_client.post('/api/v1/rules/', format='json', data=post_data,
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        self.assertEquals(resp.status_code, 204)
        found = Rules.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].version, "0")

    def test_uploading_single_rules(self):
        found = Rules.objects()
        self.assertEquals(len(found), 0)

        version = "test version a.b"
        data = "here's the data"
        r = Rules()
        r.version = version
        r.data = data

        example = {"objects":[r]}
        post_data = utils.obj_to_json(example)
        LOG.info("Calling api for rules import with post data: '%s'" % (post_data))
        resp = self.raw_api_client.post('/api/v1/rules/', format='json', data=post_data,
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        LOG.info("Status Code: %s, Response: %s" % (resp.status_code, resp))
        self.assertEquals(resp.status_code, 204)
        # Now check that the server api saved the object as expected
        found = Rules.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].version, version)
        self.assertEquals(found[0].data, data)

    def test_uploading_duplicate(self):
        found = Rules.objects()
        self.assertEquals(len(found), 0)
        version = "test version a.b"
        data = "here's the data"
        r = Rules()
        r.version = version
        r.data = data
        r.save()  # <-- main diff from above test_single....

        example = {"objects":[r]}
        post_data = utils.obj_to_json(example)
        LOG.info("Calling api for rules import with post data: '%s'" % (post_data))
        resp = self.raw_api_client.post('/api/v1/rules/', format='json', data=post_data,
                                        SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        LOG.info("Status Code: %s, Response: %s" % (resp.status_code, resp))
        self.assertEquals(resp.status_code, 204)
        # Now check that the server api saved the object as expected
        found = Rules.objects()
        self.assertEquals(len(found), 1)  # <-- ensure we didn't save a dup
        self.assertEquals(found[0].version, version)
        self.assertEquals(found[0].data, data)

    def test_upload_older_product(self):
        ##
        #  We want to accept an older upload, this is diff than most of the other API tests
        ##
        found = Rules.objects()
        self.assertEquals(len(found), 0)
        version = "1"
        data = "here's the data"
        newer = Rules()
        newer.version = version
        newer.data = data
        newer.save()  # <-- main diff from above test_single....

        older = Rules()
        older.version = "0"
        older.data = "older data"

        example = {"objects":[older]}
        post_data = utils.obj_to_json(example)
        LOG.info("Calling api for rules import with post data: '%s'" % (post_data))
        resp = self.raw_api_client.post('/api/v1/rules/', format='json', data=post_data,
                                        SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        LOG.info("Status Code: %s, Response: %s" % (resp.status_code, resp))
        self.assertEquals(resp.status_code, 204)
        # Now check that the server api saved the object as expected
        found = Rules.objects()
        self.assertEquals(len(found), 2)
        self.assertEquals(found[0].version, newer.version)
        self.assertEquals(found[0].data, newer.data)

    def test_upload_newer_product(self):
        ##
        # A newer version will be saved, but not it doesn't delete the older, this is diff than other API tests
        ##
        found = Rules.objects()
        self.assertEquals(len(found), 0)

        older = Rules()
        older.version = "0"
        older.data = "older data"
        older.save()

        version = "1"
        data = "here's the data"
        newer = Rules()
        newer.version = version
        newer.data = data

        example = {"objects":[newer]}
        post_data = utils.obj_to_json(example)
        LOG.info("Calling api for rules import with post data: '%s'" % (post_data))
        resp = self.raw_api_client.post('/api/v1/rules/', format='json', data=post_data,
                                        SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        LOG.info("Status Code: %s, Response: %s" % (resp.status_code, resp))
        self.assertEquals(resp.status_code, 204)
        # Now check that the server api saved the object as expected
        found = Rules.objects()
        self.assertEquals(len(found), 2)
        for item in found:
            self.assertIn(item.version, (newer.version, older.version))
