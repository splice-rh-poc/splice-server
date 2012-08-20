from entitlement.models import ConsumerIdentity, ReportingItem, ProductUsage

import logging
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
    def get_entitlement_certificate(self, identity_cert, consumer_identifier, installed_products):
        """
        @param identity_cert: str containing X509 certificate, identify of the consumer
        @type identity_cert: str

        @param consumer_identifier: a str to help uniquely identify consumers in a given network, could be MAC address
        @type consumer_identifier: str

        @param installed_products: a list of X509 certificates, identifying each product installed on the consumer
        @type products: [str]

        @return: an x509 certificate to be used as an entitlement certificate
        @rtype: str
        """
        if not self.validate_cert(identity_cert):
            raise CertValidationException()

        identity = self.extract_identifier(identity_cert)
        marketing_products = self.get_marketing_products(identity, installed_products)

        allowed_marketing_products, unallowed_marketing_products = \
            self.check_access(identity, marketing_products)

        if unallowed_marketing_products:
            raise UnallowedProducts(unallowed_marketing_products)

        self.record_usage(identity, consumer_identifier, allowed_marketing_products)

        entitlement_cert = self.request_entitlement(identity, allowed_marketing_products)
        return entitlement_cert


    def validate_cert(self, cert):
        _LOG.info("Validate the identity_certificate is signed by the expected CA")
        return True

    def extract_identifier(self, identity_cert):
        return "Dummy_identifier_value"

    def get_marketing_products(self, identity, products):
        _LOG.info("Call out to external service, determine marketing products " +
                  "associated to passed in engineering products")
        return []

    def check_access(self, identity, marketing_products):
        _LOG.info("Check if consumer identity is allowed to access these products")
        return ["allowed_product_1", "allowed_product_2"], []

    def record_usage(self, identity, consumer_identifier, marketing_products):
        _LOG.info("Record usage")
        return

    def request_entitlement(self, identity, allowed_products):
        _LOG.info("Request entitlement certificate from external service")
        return "contents of X509 string for <%s> with products <%s>" % (identity, allowed_products)