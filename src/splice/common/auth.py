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

import httplib
import logging
import oauth2

from django.http import HttpResponse
from tastypie.authentication import Authentication, MultiAuthentication
from tastypie.authorization import Authorization

from certutils.certutils import CertUtils
from splice.common import config
from splice.common.certs import get_client_cert_from_request, get_identifier_from_cert,get_splice_server_identity_ca_pem

_LOG = logging.getLogger(__name__)


class X509CertificateAuthentication(Authentication):
    """
    Class will perform authentication based on the X509 certificate used to form the SSL connection.
    The certificate will be found from the context of the request.
    If the certificate has been signed by the configured CA and it is valid the request will be authenticated.
    """
    def __init__(self, verification_ca):
        """
        @param verification_ca: CA to be used in verifying client certificates were signed correctly.
                                This is the actual string PEM encoded certificate, not a path to a file
        @type verification_ca: str, contents in PEM encoded format
        @return:
        """
        super(X509CertificateAuthentication, self).__init__(require_active=False)
        self.verification_ca = verification_ca
        self.cert_utils = CertUtils()

    def is_authenticated(self, request, **kwargs):
        """
        Verify that the SSL client certificate used to form this SSL Connection
        has been signed by the configured CA.

        @param request:
        @type django.http.HttpRequest

        @param kwargs:
        @return:
        """
        x509_cert_from_request = get_client_cert_from_request(request)
        if x509_cert_from_request:
            if self.cert_utils.validate_certificate(x509_cert_from_request, self.verification_ca):
                return True
        return False

    # Optional but recommended
    def get_identifier(self, request):
        """
        Return the UUID and Account number embedded in the certificate

        @param request:
        @return: (CN, O) corresponds to CN being the UUID of the certificate and O being the account number
        """
        x509_cert_from_request = get_client_cert_from_request(request)
        return get_identifier_from_cert(x509_cert_from_request)

class UUIDAuthorization(Authorization):
    """
    Placeholder for future authorization code when we implement 'Restricted'/'Unrestricted'
    """
    def is_authorized(self, request, object=None):
        x509_cert_from_request = get_client_cert_from_request(request)
        identity_uuid, identity_account = get_identifier_from_cert(x509_cert_from_request)
        if not identity_uuid:
            return False
        return True

class TwoLeggedOAuthAuthentication(Authentication):
    """
    Two Legged OAuth Authenticator
    """
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret

    def is_authenticated(self, request, **kwargs):
        """
        Performs two legged oauth 1.0 verification against a known key/secret

        @param request:
        @type django.http.HttpRequest

        @param kwargs:
        @return:
        """
        if not self.key or not self.secret:
            _LOG.info("OAuth key or secret not found, skipping OAuth Authentication")
            return False

        auth_header = {}
        if 'HTTP_AUTHORIZATION' in request.META:
            auth_header = {'Authorization':request.META.get('HTTP_AUTHORIZATION')}

        absolute_uri = request.build_absolute_uri()
        url = absolute_uri
        if absolute_uri.find('?') != -1:
            url = absolute_uri[:absolute_uri.find('?')]

        oauth_consumer = oauth2.Consumer(key=self.key, secret=self.secret)
        oauth_server = oauth2.Server()
        oauth_server.add_signature_method(oauth2.SignatureMethod_HMAC_SHA1())

        oauth_request = oauth2.Request.from_request(
            request.method, url, headers=auth_header, 
            parameters=dict(request.REQUEST.items()))
        if not oauth_request:
            _LOG.warn("Unable to instantiate oauth2.Request from: method=%s, url=%s, headers=%s, parameters=%s" % \
                (request.method, url, auth_header, dict(request.REQUEST.items())))
            return False

        try:
            oauth_server.verify_request(oauth_request, oauth_consumer, None)
        except oauth2.Error, e:
            _LOG.error('error verifying OAuth signature: %s' % e)
            _LOG.info("Debug info: key=<%s>, secret=<%s>" % (self.key, self.secret))
            _LOG.info("Debug info:  url = '%s'" % (url))
            _LOG.info("Debug info:  auth_header = '%s'" % (auth_header))
            _LOG.info("Debug info:  parameters = '%s'" % (request.REQUEST.items()))
            return False
        return True


class SpliceAuth(MultiAuthentication):
    def __init__(self, ca_cert=None, oauth_key=None, oauth_secret=None):
        if not ca_cert:
            ca_cert = get_splice_server_identity_ca_pem()
        x509_auth = X509CertificateAuthentication(verification_ca=ca_cert)
        self.backends = [x509_auth]
        oauth_params = config.get_oauth_params()
        if oauth_params["enabled"]:
            if not oauth_key:
                oauth_key = oauth_params["key"]
            if not oauth_secret:
                oauth_secret = oauth_params["secret"]
            two_legged_oauth = TwoLeggedOAuthAuthentication(key=oauth_key, secret=oauth_secret)
            self.backends.append(two_legged_oauth)