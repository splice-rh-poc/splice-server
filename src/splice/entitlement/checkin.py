import logging
import time
from datetime import datetime

from splice.common import candlepin_client
from splice.common.certs import CertUtils
from splice.common.config import CONFIG

from splice.entitlement.models import ConsumerIdentity, ReportingItem, ProductUsage,\
MarketingProduct, MarketingProductSubscription, SpliceServer

_LOG = logging.getLogger(__name__)

class CheckinException(Exception):
    pass

class CertValidationException(CheckinException):
    pass

class UnallowedProductException(CheckinException):
    def __init__(self, products):
        super(UnallowedProductException, self).__init__(self)
        self.products = products

    def __str__(self):
        return "Unallowed products: %s" % (products)

class CheckIn(object):
    """
    Logic for recording a consumers usage and returning an entitlement certificate
    will be implemented here.
    """
    def __init__(self):
        self.cert_utils = CertUtils()
        f = None
        try:
            self.root_ca_path = CONFIG.get("security", "root_ca_cert")
            f = open(self.root_ca_path, "r")
            self.root_ca_cert_pem = f.read()
        finally:
            if f:
                f.close()

    def get_this_server(self):
        # parse a configuration file and determine our splice server identifier
        # OR...read in a SSL cert that identifies our splice server.
        uuid="our splice server uuid"
        server = SpliceServer.objects(uuid=uuid).first()
        if not server:
            server = SpliceServer(uuid=uuid, description="Test data", hostname="somewhere.example.com:8000")
            try:
                server.save()
            except Exception, e:
                _LOG.exception(e)
        return server

    def get_entitlement_certificate(self, identity_cert, consumer_identifier, installed_products):
        """
        @param identity_cert: str containing X509 certificate, identify of the consumer
        @type identity_cert: str

        @param consumer_identifier: a str to help uniquely identify consumers in a given network, could be MAC address
        @type consumer_identifier: str

        @param installed_products: a list of X509 certificates, identifying each product installed on the consumer
        @type products: [str]

        @return:    a list of tuples, first entry is a string of the x509 certificate in PEM format,
                    second entry is the associated private key in string format
        @rtype: [(str,str)]
        """
        if not self.validate_cert(identity_cert):
            raise CertValidationException()

        identity = self.get_identity(identity_cert)

        allowed_products, unallowed_products = self.check_access(identity, installed_products)
        if unallowed_products:
            raise UnallowedProducts(unallowed_products)

        cert_info = self.request_entitlement(identity, allowed_products)
        # TODO:  Must add system facts to reporting data
        self.record_usage(identity, consumer_identifier, allowed_products)
        return cert_info

    def validate_cert(self, cert_pem):
        """
        @param cert_pem: x509 encoded pem certificate as a string
        @param cert_pem: str

        @return: true if 'cert_pem' was signed by the configured root CA, false otherwise
        @rtype: bool
        """
        _LOG.info("Validate the identity_certificate is signed by the expected CA from '%s'" % (self.root_ca_path))
        _LOG.debug(cert_pem)
        return self.cert_utils.validate_certificate_pem(cert_pem, self.root_ca_cert_pem)

    def parse_cert_subject(self, subject, target):
        items = subject.split("/")
        for pair in items:
            pieces = pair.split("=")
            if pieces[0].lower() == target.lower():
                return pieces[1]
        return None

    def extract_id_from_identity_cert(self, identity_cert):
        x509_certs = self.cert_utils.get_certs_from_string(identity_cert)
        # Grab the first cert if it exists
        if not x509_certs:
            return None
        c = x509_certs[0]
        subject = c.get_subject()
        if not subject:
            return None
        subject = subject.as_text()
        return self.parse_cert_subject(subject, "CN")

    def get_identity(self, identity_cert):
        id_from_cert = self.extract_id_from_identity_cert(identity_cert)
        _LOG.info("Found ID from identity certificate is '%s' " % (id_from_cert))
        identity = ConsumerIdentity.objects(uuid=id_from_cert).first()
        if not identity:
            identity = ConsumerIdentity(uuid=id_from_cert, subscriptions=[])
            try:
                identity.save()
            except Exception, e:
                _LOG.exception(e)
        return identity

    def check_access(self, identity, installed_products):
        """
        @param identity the consumers identity
        @type identity: splice.common.models.ConsumerIdentity

        @param installed_products list of product ids representing the installed engineering products
        @type installed_products: [str, str]]

        @return tuple of list of allowed products and list of unallowed products
        @rtype [],[]
        """
        _LOG.info("Check if consumer identity <%s> is allowed to access products: %s" % \
                  (identity, installed_products))
        return installed_products, []

    def record_usage(self, identity, consumer_identifier, marketing_products):
        """
        @param identity consumer's identity
        @type identity: str
        @param consumer_identifier means of uniquely identifying different instances with same consumer identity
            an example could be a mac address
        @type consumer_identifier: str
        @param products: list of product ids
        @type products: [entitlement.models.Product]
        """
        _LOG.info("Record usage for '%s'" % (identity))
        prod_info = []
        for mp in marketing_products:
            prod_info.append(ReportingItem(product=mp, date=datetime.now()))

        prod_usage = ProductUsage.objects(consumer=identity, splice_server=self.get_this_server(),
            instance_identifier=consumer_identifier).first()
        if not prod_usage:
            prod_usage = ProductUsage(consumer=identity, splice_server=self.get_this_server(),
                instance_identifier=consumer_identifier, product_info=[])

        # Add this checkin's usage info
        prod_usage.product_info.extend(prod_info)
        try:
            prod_usage.save()
        except Exception, e:
            _LOG.exception(e)
        return

    def request_entitlement(self, identity, allowed_products):
        cp_config = self.__get_candlepin_config_info()
        installed_products=allowed_products
        _LOG.info("Request entitlement certificate from external service: %s:%s%s for RHIC <%s> with products <%s>" % \
                  (cp_config["host"], cp_config["port"], cp_config["url"], identity.uuid, installed_products))

        cert_info = candlepin_client.get_entitlement(
            host=cp_config["host"], port=cp_config["port"], url=cp_config["url"],
            installed_products=installed_products,
            identity=identity.uuid,
            username=cp_config["username"], password=cp_config["password"])
        return cert_info

    def __get_candlepin_config_info(self):
        return {
            "host": CONFIG.get("entitlement", "host"),
            "port": CONFIG.get("entitlement", "port"),
            "url": CONFIG.get("entitlement", "url"),
            "username": CONFIG.get("entitlement", "username"),
            "password": CONFIG.get("entitlement", "password"),
        }
