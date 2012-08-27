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

import datetime
import logging
import time
import os

from glob import glob
from M2Crypto import X509, BIO

LOG = logging.getLogger(__name__)
try:
    from M2Crypto.X509 import CRL_Stack
    M2CRYPTO_HAS_CRL_SUPPORT = True
except:
    M2CRYPTO_HAS_CRL_SUPPORT = False
    LOG.warning("**M2Crypto<%s> lacks patch for using Certificate Revocation Lists**")

from splice.common.config import CONFIG

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
        #utils = CertUtils()
        #return utils.get_certs_from_string(cert_string)
    return None

class CertUtils:

    def __init__(self, config=None):
        if not config:
            self.config = CONFIG
        self.log_failed_cert = True
        self.log_failed_cert_verbose = True
        self.max_num_certs_in_chain = 100
        try:
            self.log_failed_cert = self.config.get('main', 'log_failed_cert')
        except:
            pass
        try:
            self.log_failed_cert_verbose = self.config.get('main', 'log_failed_cert_verbose')
        except:
            pass
        try:
            self.max_num_certs_in_chain = self.config.getint('main', 'max_num_certs_in_chain')
        except:
            pass

    def validate_certificate(self, cert_filename, ca_filename):
        '''
        Validates a certificate against a CA certificate.
        Input expects filenames.
        
        @param cert_filename: full path to the PEM encoded certificate to validate
        @type  cert_filename: str

        @param ca_filename: full path to the PEM encoded CA certificate
        @type  ca_filename: str

        @return: true if the certificate was signed by the given CA; false otherwise
        @rtype:  boolean
        '''
        f = open(ca_filename)
        try:
            ca_data = f.read()
        finally:
            f.close()
        f = open(cert_filename)
        try:
            cert_data = f.read()
        finally:
            f.close()
        return self.validate_certificate_pem(cert_data, ca_data)

    def validate_certificate_pem(self, cert_pem, ca_pem, crl_pems=None, check_crls=True, crl_dir=None):
        '''
        Validates a certificate against a CA certificate and CRLs if they exist.
        Input expects PEM encoded strings.

        @param cert_pem: PEM encoded certificate
        @type  cert_pem: str

        @param ca_pem: PEM encoded CA certificates, allows chain of CA certificates if concatenated together
        @type  ca_pem: str

        @param crl_pems: List of CRLs, each CRL is a PEM encoded string
        @type  crl_pems: List[str]

        @param check_crls: Defaults to True, if False will skip CRL check
        @type  check_crls: boolean

        @param crl_dir: Path to search for CRLs, default is None which defaults to configuration file parameter
        @type  crl_dir: str

        @return: true if the certificate was signed by the given CA; false otherwise
        @rtype:  boolean
        '''
        cert = X509.load_cert_string(cert_pem)
        if not M2CRYPTO_HAS_CRL_SUPPORT:
            # Will only be able to use first CA from the ca_pem if it was a chain
            ca_cert = X509.load_cert_string(ca_pem)
            return cert.verify(ca_cert.get_pubkey())
        ca_chain = self.get_certs_from_string(ca_pem)
        crl_stack = X509.CRL_Stack()
        if check_crls:
            for ca in ca_chain:
                ca_hash = ca.get_issuer().as_hash()
                stack = self.get_crl_stack(ca_hash, crl_dir=crl_dir)
                for c in stack:
                    crl_stack.push(c)
            if crl_pems:
                for c in crl_pems:
                    crl_stack.push(X509.load_crl_string(c))
        return self.x509_verify_cert(cert, ca_chain, crl_stack)

    def x509_verify_cert(self, cert, ca_certs, crl_stack=None):
        """
        Validates a Certificate against a CA Certificate and a Stack of CRLs

        @param  cert:  Client certificate to verify
        @type   cert:  M2Crypto.X509.X509

        @param  ca_certs:  Chain of CA Certificates
        @type   ca_certs:  [M2Crypto.X509.X509]

        @param  crl_stack: Stack of CRLs, default is None
        @type   crl_stack: M2Crypto.X509.CRL_Stack

        @return: true if the certificate is verified by OpenSSL APIs, false otherwise
        @rtype:  boolean
        """
        store = X509.X509_Store()
        for ca in ca_certs:
            store.add_cert(ca)
        if crl_stack and len(crl_stack) > 0:
            store.set_flags(X509.m2.X509_V_FLAG_CRL_CHECK |
                       X509.m2.X509_V_FLAG_CRL_CHECK_ALL)
        store_ctx = X509.X509_Store_Context()
        store_ctx.init(store, cert)
        if crl_stack and len(crl_stack) > 0:
            store_ctx.add_crls(crl_stack)
        retval = store_ctx.verify_cert()
        if retval != 1:
            msg = "Cert verification failed against %s ca cert(s) and %s CRL(s)" % (len(ca_certs), len(crl_stack))
            if self.log_failed_cert:
                msg += "\n%s" % (self.get_debug_info_certs(cert, ca_certs, crl_stack))
            LOG.info(msg)
        return retval

    def get_crl_stack(self, issuer_hash, crl_dir=None):
        """
        @param issuer_hash: Hash value of the issuing certificate
        @type  issuer_hash: unsigned long

        @param crl_dir: Path to search for CRLs, default is None which defaults to configuration file parameter
        @type  crl_dir: str

        @return CRL_Stack of any CRLs issued by the issuer_hash
        @rtype: CRL_Stack: M2Crypto.X509.CRL_Stack
        """
        crl_stack = X509.CRL_Stack()
        if not crl_dir:
            crl_dir = self._crl_directory()
        if os.path.exists(crl_dir):
            search_path = "%s/%x.r*" % (crl_dir, issuer_hash)
            crl_paths = glob(search_path)
            for c in crl_paths:
                try:
                    crl = X509.load_crl(c)
                    crl_stack.push(crl)
                except:
                    LOG.exception("Unable to load CRL file: %s" % (c))
        return crl_stack

    def get_certs_from_string(self, data):
        """
        @param data: A single string of concatenated X509 Certificates in PEM format
        @type data: str

        @return list of X509 Certificates
        @rtype: [M2Crypto.X509.X509]
        """
        # Refer to OpenSSL crypto/x509/by_file.c
        # Function: X509_load_cert_file() to see how they parse a chain file and add
        # the certificates to a X509_Store.  Below follows a similar procedure.
        bio = BIO.MemoryBuffer(data)
        certs = []
        try:
            if not M2CRYPTO_HAS_CRL_SUPPORT:
                # Old versions of M2Crypto behave differently and would loop indefinitely over load_cert_bio
                return X509.load_cert_string(data)
            for index in range(0, self.max_num_certs_in_chain):
                # Read one cert at a time, 'bio' stores the last location read
                # Exception is raised when no more cert data is available
                cert = X509.load_cert_bio(bio)
                if not cert:
                    # This is likely to never occur, a X509Error should always be raised
                    break
                certs.append(cert)
                if index == (self.max_num_certs_in_chain - 1):
                    LOG.info("**WARNING** Pulp reached maximum number of <%s> certs supported in a chain." % (self.max_num_certs_in_chain))

        except X509.X509Error:
            # This is the normal return path.
            return certs
        return certs

    def get_debug_info_certs(self, cert, ca_certs, crl_stack):
        """
        Debug method to display information certificates.  Typically used to print info after a verification failed.
        @param cert: a X509 certificate
        @type cert: M2Crypto.X509.X509

        @param ca_certs: list of X509 CA certificates
        @type ca_certs: [M2Crypto.X509.X509]

        @param crl_stack: a stack of CRLs
        @type crl_stack: M2Crypto.X509.CRL_Stack

        @return: a debug message
        @rtype: str
        """
        msg = "Current Time: <%s>" % (time.asctime())
        if self.log_failed_cert_verbose:
            msg += "\n%s" % (cert.as_text())
        info = self.get_debug_X509(cert)
        msg += "\nCertificate to verify: \n\t%s" % (info)
        msg += "\nUsing a CA Chain with %s cert(s)" % (len(ca_certs))
        for ca in ca_certs:
            info = self.get_debug_X509(ca)
            msg += "\n\tCA: %s" % (info)
        msg += "\nUsing a CRL Stack with %s CRL(s)" % (len(crl_stack))
        for crl in crl_stack:
            info = self.get_debug_CRL(crl)
            msg += "\n\tCRL: %s" % (info)
        return msg

    def get_debug_X509(self, cert):
        """
        @param cert: a X509 certificate
        @type cert: M2Crypto.X509.X509

        @return: string of debug information about the passed in X509
        @rtype: str
        """
        msg = "subject=<%s>, issuer=<%s>, subject.as_hash=<%s>, issuer.as_hash=<%s>, fingerprint=<%s>, serial=<%s>, version=<%s>, check_ca=<%s>, notBefore=<%s>, notAfter=<%s>" % \
              (cert.get_subject(), cert.get_issuer(), cert.get_subject().as_hash(), cert.get_issuer().as_hash(), cert.get_fingerprint(), cert.get_serial_number(),
               cert.get_version(), cert.check_ca(), cert.get_not_before(), cert.get_not_after())
        return msg

    def get_debug_X509_Extensions(self, cert):
        """
        @param cert: a X509 certificate
        @type cert: M2Crypto.X509.X509

        @return: debug string
        @rtype: str
        """
        extensions = ""
        ext_count = cert.get_ext_count()
        for i in range(0, ext_count):
            ext = cert.get_ext_at(i)
            extensions += " %s:<%s>" % (ext.get_name(), ext.get_value())
        return extensions

    def get_debug_CRL(self, crl):
        """
        @param crl: a X509_CRL instance
        @type crl: M2Crypto.X509.CRL

        @return: string of debug information about the passed in CRL
        @rtype: str
        """
        msg = "issuer=<%s>, issuer.as_hash=<%s>" % (crl.get_issuer(), crl.get_issuer().as_hash())
        if hasattr(crl, "get_lastUpdate") and hasattr(crl, "get_nextUpdate"):
            nextUpdate = crl.get_nextUpdate()
            lastUpdate = crl.get_lastUpdate()
            msg += " lastUpdate=<%s>, nextUpdate=<%s>" % (lastUpdate, nextUpdate)
            try:
                now = datetime.datetime.now().date()
                next = nextUpdate.get_datetime().date()
                last = lastUpdate.get_datetime().date()
                if now > next:
                    msg += "\n** ** WARNING ** **: Looks like this CRL is expired.  nextUpdate = <%s>" % (nextUpdate)
                if now < last:
                    msg += "\n** ** WARNING ** **: Looks like this CRL is premature. lastUpdate = <%s>" % (lastUpdate)
            except:
                pass
        return msg

    def _crl_directory(self):
        '''
        Returns the absolute path to the directory in which
        Certificate Revocation Lists (CRLs) are stored

        @return: absolute path to a directory that may not exist
        @rtype:  str
        '''
        return self.config.get('crl', 'location')
