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

import oauth2

from django.http import HttpResponse

from splice.common import config
from splice.common.auth import X509CertificateAuthentication, TwoLeggedOAuthAuthentication

# Unit test imports
from base import BaseEntitlementTestCase


class X509CertificateAuthenticationTest(BaseEntitlementTestCase):

    def setUp(self):
        super(X509CertificateAuthenticationTest, self).setUp()
        self.x509_auth = X509CertificateAuthentication(verification_ca=self.splice_server_identity_ca_pem)
    def tearDown(self):
        super(X509CertificateAuthenticationTest, self).tearDown()

    def test_with_no_certificate(self):
        req = self.request_factory.request()
        CN, O = self.x509_auth.get_identifier(req)
        self.assertIsNone(CN)
        self.assertIsNone(O)
        self.assertFalse(self.x509_auth.is_authenticated(request=req))

    def test_with_valid_certificate(self):
        req = self.request_factory.request(SSL_CLIENT_CERT=self.valid_identity_cert_pem)
        CN, O = self.x509_auth.get_identifier(req)
        self.assertEqual(CN, self.expected_valid_splice_server_identity_uuid)
        self.assertEqual(O, self.expected_valid_splice_server_identity_num)
        self.assertTrue(self.x509_auth.is_authenticated(request=req))

    def test_with_invalid_certificate(self):
        req = self.request_factory.request(SSL_CLIENT_CERT=self.invalid_identity_cert_pem)
        self.assertFalse(self.x509_auth.is_authenticated(request=req))


class TwoLeggedOAuthAuthenticationTest(BaseEntitlementTestCase):

    def setUp(self):
        super(TwoLeggedOAuthAuthenticationTest, self).setUp()
        config_oauth_params = config.get_oauth_params()
        self.key = config_oauth_params["key"]
        self.secret = config_oauth_params["secret"]
        
    def tearDown(self):
        super(TwoLeggedOAuthAuthenticationTest, self).tearDown()

    def test_with_no_auth_headers(self):
        req = self.request_factory.request()
        two_leg_oauth = TwoLeggedOAuthAuthentication(key="keyvalue", secret="secertvalue")
        self.assertFalse(two_leg_oauth.is_authenticated(request=req))

    def test_with_valid_auth_headers(self):
        key = "unittest_key"
        secret = "unittest_secret"
        server_name = "testserver"
        path_info = "/api/v1/ping/"
        url = "http://%s%s" % (server_name, path_info)
        method = "GET"
        consumer = oauth2.Consumer(key, secret)
        oauth_request = oauth2.Request.from_consumer_and_token(
            consumer, 
            http_method=method, 
            http_url=url)
        oauth_request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, None)
        headers = oauth_request.to_header()
        # Create the request
        req = self.request_factory.request(
            REQUEST_METHOD=method,
            SERVER_NAME=server_name, 
            PATH_INFO=path_info)
        # Add OAuth parameters
        req.META['HTTP_AUTHORIZATION'] = headers['Authorization']
        two_leg_oauth = TwoLeggedOAuthAuthentication(key=key, secret=secret)
        self.assertTrue(two_leg_oauth.is_authenticated(request=req))
    
    def test_with_wrong_secret(self):
        key = "unittest_key"
        secret = "unittest_secret"
        server_name = "testserver"
        path_info = "/api/v1/ping/"
        url = "http://%s%s" % (server_name, path_info)
        method = "GET"
        consumer = oauth2.Consumer(key, secret)
        oauth_request = oauth2.Request.from_consumer_and_token(
            consumer, 
            http_method=method, 
            http_url=url)
        oauth_request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, None)
        headers = oauth_request.to_header()
        # Create the request
        req = self.request_factory.request(
            REQUEST_METHOD=method,
            SERVER_NAME=server_name, 
            PATH_INFO=path_info)
        # Add OAuth parameters
        req.META['HTTP_AUTHORIZATION'] = headers['Authorization']
        two_leg_oauth = TwoLeggedOAuthAuthentication(key=key, secret="WRONG_SECRET")
        self.assertFalse(two_leg_oauth.is_authenticated(request=req))

    def test_api_call_with_oauth(self):
        server_name = "testserver"
        path_info = "/api/v1/ping/"
        url = "http://%s%s" % (server_name, path_info)
        method = "GET"
        consumer = oauth2.Consumer(self.key, self.secret)
        oauth_request = oauth2.Request.from_consumer_and_token(
            consumer, 
            http_method=method, 
            http_url=url)
        oauth_request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, None)
        headers = oauth_request.to_header()
        resp = self.api_client.get('/api/v1/ping/', format='json', data="", authentication=headers['Authorization'])
        self.assertEquals(resp.status_code, 202)

    def test_api_call_with_oauth_wrong_secret(self):
        server_name = "testserver"
        path_info = "/api/v1/ping/"
        url = "http://%s%s" % (server_name, path_info)
        method = "GET"
        consumer = oauth2.Consumer(self.key, "WRONG_SECRET")
        oauth_request = oauth2.Request.from_consumer_and_token(
            consumer, 
            http_method=method, 
            http_url=url)
        oauth_request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, None)
        headers = oauth_request.to_header()
        resp = self.api_client.get('/api/v1/ping/', format='json', data="", authentication=headers['Authorization'])
        self.assertEquals(resp.status_code, 401)
