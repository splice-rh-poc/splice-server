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

import logging

# Unit test imports
from base import BaseEntitlementTestCase

LOG = logging.getLogger(__name__)

class EntitlementResourceTest(BaseEntitlementTestCase):

    def setUp(self):
        super(EntitlementResourceTest, self).setUp()
        self.username = "admin"
        self.password = "admin"
        # TODO add auth
        # self.user = User.objects.create_user(self.username, 'admin@example.com', self.password)
        self.post_data = {
            'consumer_identifier': "52:54:00:15:E7:69",
            'products': self.valid_products,
            'system_facts': {"tbd":"values"}
        }
        self.load_rhic_data()

    def tearDown(self):
        super(EntitlementResourceTest, self).tearDown()

    def get_credentials(self):
        return self.create_basic(username=self.username, password=self.password)

    def test_post_entitlement_valid_identity(self):
        LOG.info("Entered 'test_post_entitlement_valid_identity'")
        resp = self.api_client.post('/api/v1/entitlement/BOGUS_IDENTITY/', format='json',
            authentication=self.get_credentials(), data=self.post_data,
            SSL_CLIENT_CERT=self.valid_identity_cert_pem)
        LOG.info("Completed call to entitlement checkin from unit test: test_post_entitlement_valid_identity")
        if resp.status_code != 200:
            print resp.status_code, resp
        self.assertEquals(resp.status_code, 200)
        self.assertTrue(resp['Content-Type'].startswith('application/json'))
        self.assertValidJSON(resp.content)

        deserialized = self.deserialize(resp)
        self.assertEquals(len(deserialized["certs"]), 1)
        self.assertEquals(deserialized["certs"][0][0], self.expected_cert)
        self.assertEquals(deserialized["certs"][0][1], self.expected_key)
        self.assertEquals(deserialized["certs"][0][2], self.expected_serial)

    def test_post_entitlement_invalid_identity(self):
        resp = self.api_client.post('/api/v1/entitlement/BOGUS_IDENTITY/',
            format='json',
            authentication=self.get_credentials(),
            data=self.post_data,
            SSL_CLIENT_CERT=self.invalid_identity_cert_pem)
        self.assertHttpUnauthorized(resp)
        self.assertEqual("Unable to verify SSL client's identity certificate was signed by configured CA", resp.content)

    def test_post_entitlement_deleted_identity(self):
        resp = self.api_client.post('/api/v1/entitlement/%s/' % (self.deleted_identity_uuid),
            format='json',
            authentication=self.get_credentials(),
            data=self.post_data,
            SSL_CLIENT_CERT=self.deleted_identity_cert_pem)
        self.assertHttpGone(resp)
        self.assertEqual("Exception: consumer identity '%s' has been deleted." % (self.deleted_identity_uuid), resp.content)
