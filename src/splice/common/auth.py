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

from django.http import HttpResponse
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization

from certutils.certutils import CertUtils
from splice.common.certs import get_client_cert_from_request, get_identifier_from_cert

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
        return HttpResponse(
            content="Unable to verify consumer's identity certificate was signed by configured CA",
            status=httplib.UNAUTHORIZED)

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