# -*- coding: utf-8 -*-
#
# Copyright © 2013 Red Hat, Inc.
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
from splice.common.models import MarketingProductUsage

# Unit test imports
from base import BaseEntitlementTestCase

LOG = logging.getLogger(__name__)


class MarketingProductUsageTest(BaseEntitlementTestCase):
    def setUp(self):
        super(MarketingProductUsageTest, self).setUp()

    def tearDown(self):
        super(MarketingProductUsageTest, self).tearDown()

    def test_example_with_raw_string_data(self):
	example = {"objects":[
			{"splice_server": "foofoofoo",
			 "checkin_date": "2006-10-25 14:30:59",
			 "instance_identifier": "bar"},
			{"splice_server": "foofoofoo",
			 "checkin_date": "2007-10-25 14:40:59",
			 "facts": {"fact1": "factresult1"},
			 "instance_identifier": "barbar"}
		]}

        post_data = json.dumps(example)
        LOG.info("Post to marketing product usage with data: %s" % (post_data))
        resp = self.raw_api_client.post('/api/v1/marketingproductusage/', format='json', data=post_data,
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        LOG.info("Response: %s" % (resp))
        self.assertEquals(resp.status_code, 204)
        found = MarketingProductUsage.objects()
        self.assertEquals(len(found), 2)
        self.assertIn(found[0].instance_identifier, ("bar", "barbar"))

    def test_uploading_duplicate(self):
        found = MarketingProductUsage.objects()
        self.assertEquals(len(found), 0)

        datestr = "2012-12-06T11:13:06.432367"
        mpu = MarketingProductUsage()
	mpu.instance_identifier="instance-1"
	mpu.splice_server = "ss-1"
	mpu.checkin_date=datestr
        mpu.save()

        self.assertEquals(len(found), 1)
        example = {"objects":[mpu]}
        post_data = utils.obj_to_json(example)
        LOG.info("Calling api for marketing product usage import with post data: '%s'" % (post_data))
        resp = self.raw_api_client.post('/api/v1/marketingproductusage/', format='json', data=post_data,
                                        SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        self.assertEquals(resp.status_code, 204)
        # Now check that the server api saved the object as expected
        found = MarketingProductUsage.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].instance_identifier, mpu.instance_identifier)

