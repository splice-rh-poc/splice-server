#
# Copyright (c) 2012 Red Hat, Inc.
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

from splice.common import config
from certutils.certutils import CertUtils, CertFileUtils, CertificateParseException

_LOG = logging.getLogger(__name__)

def get_rhic_ca_pem():
    ca_path = config.get_rhic_ca_path()
    cert_utils = CertFileUtils()
    ca_pem = cert_utils.read_pem(pem_path=ca_path)
    return ca_pem

def get_splice_server_identity_cert_path():
    return config.get_splice_server_identity_cert_path()

def get_splice_server_identity_key_path():
    return config.get_splice_server_identity_key_path()

def get_splice_server_identity(cert_pem = None):
    if not cert_pem:
        cert_pem = get_splice_server_identity_cert_pem()
    (cn, o) = get_identifier_from_cert(cert_pem)
    return cn

def get_splice_server_identity_cert_pem():
    cert_path = get_splice_server_identity_cert_path()
    cert_utils = CertFileUtils()
    cert_pem = cert_utils.read_pem(pem_path=cert_path)
    return cert_pem

def get_splice_server_identity_ca_pem():
    ca_path = config.get_splice_server_identity_ca_path()
    cert_utils = CertFileUtils()
    ca_pem = cert_utils.read_pem(pem_path=ca_path)
    return ca_pem

def get_client_cert_from_request(request):
    """
    @param request
    @type django.http.HttpRequest

    @return certificate as a string or None if no cert data was found
            looks for request.META["SSL_CLIENT_CERT"] which is inserted by mod_wsgi
    @rtype: str
    """
    if request.META.has_key("SSL_CLIENT_CERT"):
        cert_string = request.META["SSL_CLIENT_CERT"]
        return cert_string
    return None

def get_identifier_from_cert(x509_cert):
    """
    Returns the 'CN' and 'O' pieces of the passed in Certificate if available
    @param x509_cert:
    @return: (str, str)
    """
    cn = None
    o = None
    cert_utils = CertUtils()
    try:
        subj_pieces = cert_utils.get_subject_pieces(x509_cert)
    except CertificateParseException:
        return None, None
    if subj_pieces:
        if subj_pieces.has_key("CN"):
            cn = subj_pieces["CN"]
        if subj_pieces.has_key("O"):
            o = subj_pieces["O"]
    return (cn, o)