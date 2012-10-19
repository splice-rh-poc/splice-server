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

from datetime import timedelta
from datetime import datetime
from dateutil.tz import tzutc
import logging

from splice.common.exceptions import UnexpectedStatusCodeException, NotFoundConsumerIdentity
from splice.common.models import ConsumerIdentity, RHICLookupTask

# Unit test imports
from base import BaseEntitlementTestCase

LOG = logging.getLogger(__name__)


class CheckInTest(BaseEntitlementTestCase):
    """
    Tests to exercise splice.entitlement.checkin.CheckIn
    """
    def setUp(self):
        super(CheckInTest, self).setUp()
        self.load_rhic_data()

    def tearDown(self):
        super(CheckInTest, self).tearDown()

    def test_validate_cert_valid(self):
        self.assertTrue(self.checkin.validate_cert(self.valid_identity_cert_pem))

    def test_validate_cert_invalid(self):
        self.assertFalse(self.checkin.validate_cert(self.invalid_identity_cert_pem))

    def test_extract_id_from_identity_cert(self):
        # below is example of subject from test data
        # $ openssl x509 -subject -in test_data/valid_cert/sample_rhic_valid.pem
        #        subject=/CN=dbcbc8e1-5b37-4a77-9db1-faf4ef29307d
        self.assertEquals(
            self.checkin.extract_id_from_identity_cert(self.valid_identity_cert_pem),
            self.expected_valid_identity_uuid)

    def test_check_access_allowed(self):
        identity = ConsumerIdentity.objects(uuid=self.valid_identity_uuid).first()
        allowed_products, unallowed_products = self.checkin.check_access(identity, self.valid_products)
        for p in self.valid_products:
            self.assertTrue(p in allowed_products)
        self.assertEquals(len(unallowed_products), 0)

    def test_check_access_unallowed(self):
        identity = ConsumerIdentity.objects(uuid=self.valid_identity_uuid).first()
        allowed_products, unallowed_products = self.checkin.check_access(identity, ["100", "101"])
        self.assertTrue("100" in unallowed_products)
        self.assertTrue("101" in unallowed_products)
        self.assertEquals(len(allowed_products), 0)

        allowed_products, unallowed_products = self.checkin.check_access(identity, [self.valid_products[0], "101"])
        self.assertTrue(self.valid_products[0] in allowed_products)
        self.assertTrue("101" in unallowed_products)
        self.assertEquals(len(allowed_products), 1)
        self.assertEquals(len(unallowed_products), 1)

    def test_not_found(self):
    # Create a stored rhic lookup that is valid and set response to 404
        rhic_uuid = "11a1aa11-a11a-1a11-111a-a22222222222"
        task = RHICLookupTask(uuid=rhic_uuid, completed=True,
            initiated=datetime.now(tzutc()),
            modified=datetime.now(tzutc()),
            status_code=404)
        task.save()
        # Verify we return this '404'
        caught = False
        try:
            self.checkin.get_identity_object(rhic_uuid)
        except NotFoundConsumerIdentity, e:
            caught = True
        self.assertTrue(caught)

    def test_unexpected_cached_status_code(self):
        # Create a stored rhic lookup that is valid and set response to 483
        # Verify we return this 'unexpected status code'
        rhic_uuid = "11a1aa11-a11a-1a11-111a-a22222222222"
        task = RHICLookupTask(uuid=rhic_uuid, completed=True,
            initiated=datetime.now(tzutc()),
            modified=datetime.now(tzutc()),
            status_code=483)
        task.save()
        caught = False
        try:
            self.checkin.get_identity_object(rhic_uuid)
        except UnexpectedStatusCodeException, e:
            caught = True
            self.assertEqual(e.status_code, 483)
        self.assertTrue(caught)
