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
import StringIO
import gzip

from splice.common import utils
from splice.common.models import MarketingProductUsage

# Unit test imports
from base import BaseEntitlementTestCase

LOG = logging.getLogger(__name__)


class JsonGzipSerializerTest(BaseEntitlementTestCase):
    def setUp(self):
        super(JsonGzipSerializerTest, self).setUp()

    def tearDown(self):
        super(JsonGzipSerializerTest, self).tearDown()

    def test_deserialize_json(self):
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

    def test_deserialize_json_gzip(self):
	example = {"objects":[
			{"splice_server": "foofoofoo",
			 "checkin_date": "2006-10-25 14:30:59",
			 "instance_identifier": "bar"},
			{"splice_server": "foofoofoo",
			 "checkin_date": "2007-10-25 14:40:59",
			 "facts": {"fact1": "factresult1"},
			 "instance_identifier": "barbar"}
		]}

        post_data = self._gzip_data(json.dumps(example))
        LOG.info("Post to marketing product usage with data: %s" % (post_data))
        resp = self.raw_api_client.post('/api/v1/marketingproductusage/', format='json', data=post_data,
            SSL_CLIENT_CERT=self.expected_valid_splice_server_identity_pem)
        LOG.info("Response: %s" % (resp))
        self.assertEquals(resp.status_code, 204)

    def _gzip_data(self, input):
        out = StringIO.StringIO()
        f = gzip.GzipFile(fileobj=out, mode='w')
        try:
            f.write(input)
        finally:
            f.close()
        ret_val = out.getvalue()
        return ret_val

