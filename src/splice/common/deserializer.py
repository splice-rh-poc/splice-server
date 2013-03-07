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

import logging
import simplejson
import pprint
import gzip
import time
import StringIO
from tastypie.serializers import Serializer

_LOG = logging.getLogger(__name__)

class JsonGzipSerializer(Serializer):

    def from_json(self, content):
        try:
            start_unzip = time.time()
            data_str = StringIO.StringIO(content)
            gzipper = gzip.GzipFile(fileobj=data_str)
            data = gzipper.read()
            end_unzip = time.time()
            _LOG.info("uncompressed %.2f KB to %.2f KB in %.2f seconds" %
                      (len(content)/float(1024),
                       len(data)/float(1024), end_unzip - start_unzip))
            content = data
        except IOError:
            # if gunzipping failed, proceed anyway
            _LOG.debug("unable to gunzip output, proceeding with json decoding")
            pass
        data = simplejson.loads(content)
        return data
	

