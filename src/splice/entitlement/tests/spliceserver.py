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
from splice.common.models import SpliceServer

# Unit test imports
from base import BaseEntitlementTestCase

LOG = logging.getLogger(__name__)


class SpliceServerTest(BaseEntitlementTestCase):
    def setUp(self):
        super(SpliceServerTest, self).setUp()

    def tearDown(self):
        super(SpliceServerTest, self).tearDown()

    def test_date_as_string_is_converted_on_save(self):
        found = SpliceServer.objects()
        self.assertEquals(len(found), 0)

        server = SpliceServer()
        server.uuid = "Splice Server Test UUID-1"
        server.description = "Description data"
        server.hostname = "server.example.com"
        server.environment = "environment info"
        server.created = "2012-12-06T11:13:06.432367"
        server.modified = "2012-12-06T11:13:06.432367"
        server.save()

        found = SpliceServer.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, server.uuid)
        self.assertEquals(found[0].description, server.description)
        self.assertEquals(found[0].hostname, server.hostname)
        self.assertEquals(found[0].environment, server.environment)
        self.assertIsNotNone(found[0].created)
        self.assertEquals(type(found[0].created), datetime.datetime)
        self.assertIsNotNone(found[0].modified)
        self.assertEquals(type(found[0].modified), datetime.datetime)

    def test_get_splice_server_metadata_collection(self):
        a = SpliceServer(uuid="uuid a", description="descr a",
            hostname="a.example.com", environment="environment a")
        a.save()
        b = SpliceServer(uuid="uuid b", description="descr b",
            hostname="b.example.com", environment="environment b")
        b.save()
        resp = self.api_client.get('/api/v1/spliceserver/', format='json',
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        self.assertEquals(resp.status_code, 200)
        LOG.info("Response for GET spliceserver: Status Code: %s, Response: %s" % (resp.status_code, resp))

    def test_example_with_raw_string_data(self):
        example = {"objects": [
            {"created": "2012-12-07T15:35:54.448000", "description": "descr a",
            "environment": "environment a", "hostname": "a.example.com",
            "id": "50c20cda5c99cb55d9000001", "modified": "2012-12-07T15:35:54.448000",
            "resource_uri": "/api/v1/spliceserver/50c20cda5c99cb55d9000001/",
            "uuid": "uuid a"},

            {"created": "2012-12-07T15:35:54.686000", "description": "descr b",
            "environment": "environment b", "hostname": "b.example.com",
            "id": "50c20cda5c99cb55d9000002", "modified": "2012-12-07T15:35:54.686000",
            "resource_uri": "/api/v1/spliceserver/50c20cda5c99cb55d9000002/",
            "uuid": "uuid b"
            }]}
        post_data = json.dumps(example)
        resp = self.raw_api_client.post('/api/v1/spliceserver/', format='json', data=post_data,
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        self.assertEquals(resp.status_code, 204)
        found = SpliceServer.objects()
        self.assertEquals(len(found), 2)
        self.assertIn(found[0].uuid, ("uuid a", "uuid b"))

    def test_uploading_single_spliceserver(self):
        found = SpliceServer.objects()
        self.assertEquals(len(found), 0)

        server = SpliceServer()
        server.uuid = "Splice Server Test UUID-1"
        server.description = "Description data"
        server.hostname = "server.example.com"
        server.environment = "environment info"

        example = {"objects":[server]}
        post_data = utils.obj_to_json(example)
        LOG.info("Calling api for spliceserver import with post data: '%s'" % (post_data))
        resp = self.raw_api_client.post('/api/v1/spliceserver/', format='json', data=post_data,
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        LOG.info("Response for spliceserver import: Status Code: %s, Response: %s" % (resp.status_code, resp))
        self.assertEquals(resp.status_code, 204)
        # Now check that the server api saved the object as expected
        found = SpliceServer.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, server.uuid)
        self.assertEquals(found[0].description, server.description)
        self.assertEquals(found[0].hostname, server.hostname)
        self.assertEquals(found[0].environment, server.environment)
        self.assertIsNotNone(found[0].created)
        self.assertIsNotNone(found[0].modified)

    def test_uploading_duplicate(self):
        found = SpliceServer.objects()
        self.assertEquals(len(found), 0)

        server = SpliceServer()
        server.uuid = "Splice Server Test UUID-1"
        server.description = "Description data"
        server.hostname = "server.example.com"
        server.environment = "environment info"
        # Note this tests save()'s the instance to the DB
        server.save()
        self.assertIsNotNone(server.modified.tzinfo)

        example = {"objects":[server]}
        post_data = utils.obj_to_json(example)
        LOG.info("Calling api for spliceserver import with post data: '%s'" % (post_data))
        resp = self.raw_api_client.post('/api/v1/spliceserver/', format='json', data=post_data,
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        LOG.info("Response for spliceserver import: Status Code: %s, Response: %s" % (resp.status_code, resp))
        self.assertEquals(resp.status_code, 204)
        # Now check that the server api saved the object as expected
        found = SpliceServer.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, server.uuid)
        self.assertEquals(found[0].description, server.description)
        self.assertEquals(found[0].hostname, server.hostname)
        self.assertEquals(found[0].environment, server.environment)
        self.assertIsNotNone(found[0].created)
        self.assertIsNotNone(found[0].modified)

    def test_upload_older_spliceserver(self):
        found = SpliceServer.objects()
        self.assertEquals(len(found), 0)
        # Create 'newer' server and save to DB
        orig_uuid = "Splice Server UUID"
        orig_description = "Original Description"
        orig_hostname = "Original.hostname.com"
        orig_environment = "Original environment"
        newer = SpliceServer()
        newer.uuid = orig_uuid
        newer.description = orig_description
        newer.hostname = orig_hostname
        newer.environment = orig_environment
        newer.created = "2011-01-01T11:13:06.432367"
        newer.modified = "2012-12-01T11:13:06.432367"
        newer.save()
        found = SpliceServer.objects()
        self.assertEquals(len(found), 1)

        # Create 'older' which is one month older than newer
        older = SpliceServer()
        older.uuid = orig_uuid
        older.description = "Updated description"
        older.hostname = "updated.server.example.com"
        older.environment = "Updated environment info"
        older.created = "2011-01-01T11:13:06.432367"
        older.modified = "2012-11-01T11:13:06.432367"

        example = {"objects": [older._data]}
        post_data = utils.obj_to_json(example)
        LOG.info("Calling api for spliceserver import with post data: '%s'" % (post_data))
        resp = self.raw_api_client.post('/api/v1/spliceserver/', format='json', data=post_data,
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        LOG.info("Response for spliceserver import: Status Code: %s, Response: %s" % (resp.status_code, resp))
        self.assertEquals(resp.status_code, 204)
        # Now check that the server api kept the 'newer' as is and ignored the older
        found = SpliceServer.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, orig_uuid)
        self.assertEquals(found[0].description, orig_description)
        self.assertEquals(found[0].hostname, orig_hostname)
        self.assertEquals(found[0].environment, orig_environment)
        self.assertEquals(str(found[0].modified), "2012-12-01 11:13:06.432000+00:00")

    def test_upload_newer_spliceserver(self):
        found = SpliceServer.objects()
        self.assertEquals(len(found), 0)
        # Create 'newer' server and save to DB
        orig_uuid = "Splice Server UUID"
        orig_description = "Original Description"
        orig_hostname = "Original.hostname.com"
        orig_environment = "Original environment"
        older = SpliceServer()
        older.uuid = orig_uuid
        older.description = orig_description
        older.hostname = orig_hostname
        older.environment = orig_environment
        older.created = "2011-01-01T11:13:06.432367"
        older.modified = "2012-12-01T11:13:06.432367"
        older.save()
        found = SpliceServer.objects()
        self.assertEquals(len(found), 1)

        # Create 'older' which is one month older than newer
        newer = SpliceServer()
        newer.uuid = orig_uuid
        newer.description = "Updated description"
        newer.hostname = "updated.server.example.com"
        newer.environment = "Updated environment info"
        newer.created = "2011-01-01T11:13:06.432367"
        newer.modified = "2012-12-31T11:13:06.432367"

        example = {"objects": [newer]}
        post_data = utils.obj_to_json(example)
        LOG.info("Calling api for spliceserver import with post data: '%s'" % (post_data))
        resp = self.raw_api_client.post('/api/v1/spliceserver/', format='json', data=post_data,
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        LOG.info("Response for spliceserver import: Status Code: %s, Response: %s" % (resp.status_code, resp))
        self.assertEquals(resp.status_code, 204)
        # Now check that the server api kept the 'newer' as is and ignored the older
        found = SpliceServer.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, orig_uuid)
        self.assertEquals(found[0].description, newer.description)
        self.assertEquals(found[0].hostname, newer.hostname)
        self.assertEquals(found[0].environment, newer.environment)
        self.assertEquals(str(found[0].modified), "2012-12-31 11:13:06.432000+00:00")
