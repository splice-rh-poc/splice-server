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

from splice.common import candlepin_client


# Unit test imports
from base import BaseEntitlementTestCase


class CandlepinClientTest(BaseEntitlementTestCase):

    def setUp(self):
        super(CandlepinClientTest, self).setUp()

    def tearDown(self):
        super(CandlepinClientTest, self).tearDown()

    def test_get_entitlement(self):
        cert_info = candlepin_client.get_entitlement(host="localhost", port=0, url="mocked",
            requested_products=[4], identity="dummy identity", username="", password="")
        self.assertEquals(len(cert_info), 1)
        self.assertEquals(cert_info[0][0], self.expected_cert)
        self.assertEquals(cert_info[0][1], self.expected_key)