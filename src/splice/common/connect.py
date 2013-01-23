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

import base64
import gzip
import httplib
import logging
import simplejson as json
import StringIO
from M2Crypto import SSL, httpslib

from splice.common import utils

# Hack to work around M2Crypto.SSL.Checker.WrongHost
# seen when a remote server's SSL cert does not match their hostname
SSL.Connection.clientPostConnectionCheck = None

_LOG = logging.getLogger(__name__)

class BaseConnection(object):
    def __init__(self, host, port, handler, username=None,
                 password=None, https=True, cert_file=None, key_file=None, ca_cert=None, accept_gzip=False):
        self.host = host
        self.port = int(port)
        self.handler = handler
        self.headers = {"Content-type":"application/json",
                        "Accept": "application/json"}
        self.https = https
        self.username = username
        self.password = password
        self.cert_file = cert_file
        self.cert_key = key_file
        self.ca_cert  = ca_cert
        self.accept_gzip = accept_gzip
        if self.accept_gzip:
            self.headers['Accept-Encoding'] = 'gzip'

    def set_basic_auth(self):
        raw = ':'.join((self.username, self.password))
        encoded = base64.encodestring(raw)[:-1]
        self.headers['Authorization'] = 'Basic ' + encoded

    def set_ssl_context(self):
        context = SSL.Context("tlsv1")
        if self.ca_cert:
            context.load_verify_info(self.ca_cert)
        if self.cert_file:
            context.load_cert(self.cert_file, keyfile=self.cert_key)
        return context

    def __get_connection(self):
        conn = None
        if self.https:
            # initialize a context for ssl connection
            context = self.set_ssl_context()
            # ssl connection
            conn = httpslib.HTTPSConnection(self.host, self.port, ssl_context=context)
        else:
            conn = httplib.HTTPConnection(self.host, self.port)
        return conn

    def _gzip_data(self, input):
        out = StringIO.StringIO()
        f = gzip.GzipFile(fileobj=out, mode='w')
        try:
            f.write(input)
        finally:
            f.close()
        ret_val = out.getvalue()
        return ret_val

    def _request(self, request_type, method, body=None, gzip_body=False):
        """

        @param request_type: HTTP request such as 'GET', 'PUT', 'POST'
        @param method: combined with the URL specified by 'handler' to form the full URL end point
        @param body: contents of this request
        @param gzip_body: optional boolean, default value 'false' leaves body as is
                          'true' will compress the body
        @return:
        """
        if self.username and self.password:
            # add the basic auth info to headers
            self.set_basic_auth()
        conn = self.__get_connection()
        url = self.handler + method
        headers = self.headers
        if body:
            # Use customized JSON encoder to handle Mongo objects
            body = utils.obj_to_json(body)
            if gzip_body:
                headers["content-encoding"] = "gzip"
                orig_body = body
                body = self._gzip_data(body)
                _LOG.info("Request to '%s' compressed body from %s to %s" % (url, len(orig_body), len(body)))

        _LOG.info("Sending '%s' to '%s' \n\twith headers '%s'" % (request_type, url, headers))
        conn.request(request_type, url, body=body, headers=headers)
        response = conn.getresponse()
        response_body = response.read()
        if response.getheader('content-encoding', '') == 'gzip':
            data = StringIO.StringIO(response_body)
            gzipper = gzip.GzipFile(fileobj=data)
            response_body = gzipper.read()
        _LOG.info("Received '%s' from '%s %s'" % (response.status, request_type, url))
        if response.status in [200, 202] and response_body:
            _LOG.info("Response body = \n'%s'" % (response_body))
            response_body = json.loads(response_body)
        return response.status, response_body

    def GET(self, method):
        return self._request("GET", method)

    def POST(self, method, params="", gzip_body=False):
        return self._request("POST", method, params, gzip_body)
