from splice.entitlement.models import ConsumerIdentity, ReportingItem, ProductUsage, \
    MarketingProduct, MarketingProductSubscription, SpliceServer

from datetime import datetime
import logging
import time

from splice.common import candlepin_client

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

    def get_this_server(self):
        # parse a configuration file and determine our splice server identifier
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

        @return: an x509 certificate to be used as an entitlement certificate
        @rtype: str
        """
        if not self.validate_cert(identity_cert):
            raise CertValidationException()

        identity = self.get_identity(identity_cert)
        marketing_products = self.get_marketing_products(identity, installed_products)

        allowed_marketing_products, unallowed_marketing_products = \
            self.check_access(identity, marketing_products)
        if unallowed_marketing_products:
            raise UnallowedProducts(unallowed_marketing_products)

        cert_info = self.request_entitlement(identity, allowed_marketing_products)
        self.record_usage(identity, consumer_identifier, allowed_marketing_products)
        return cert_info


    def validate_cert(self, cert):
        _LOG.info("Validate the identity_certificate is signed by the expected CA")
        return True

    def get_identity(self, identity_cert):
        # Convert the string to a X509 certificate
        # extract the CN from the X509 certificate
        # Lookup if a Consumer exists with this identifier
        #   If not found initiate a lookup through parent chain for this ID
        #         return a retry status code in ~3 minutes.
        # Return ConsumerIdentity instance
        uuid = "admin" # hard coding 'admin' for now since candlepin is configured for this as the RHIC
        identity = ConsumerIdentity.objects(uuid=uuid).first()
        if not identity:
            identity = ConsumerIdentity(uuid=uuid, subscriptions=[])
            try:
                identity.save()
            except Exception, e:
                _LOG.exception(e)
        return identity

    def get_marketing_products(self, identity, products):
        _LOG.info("Call out to external service, determine marketing products " +
                  "associated to passed in engineering products")
        mp1_id = "dummy_value_1"
        mp1_name = "dummy_value_name_1"
        mp1_description = "dummy_value_description_1"
        mp2_id = "dummy_value_2"
        mp2_name = "dummy_value_name_2"
        mp2_description = "dummy_value_descripion_2"

        mp1 = MarketingProduct.objects(uuid=mp1_id, name=mp1_name, description=mp1_description).first()
        if not mp1:
            mp1 = MarketingProduct(uuid=mp1_id, name=mp1_name, description=mp1_description)
            try:
                mp1.save()
            except Exception,e:
                _LOG.exception(e)
        mp2 = MarketingProduct.objects(uuid=mp2_id, name=mp2_name, description=mp2_description).first()
        if not mp2:
            mp2 = MarketingProduct(uuid=mp2_id, name=mp2_name, description=mp2_description)
            try:
                mp2.save()
            except Exception, e:
                _LOG.exception(e)
        return [mp1, mp2]

    def check_access(self, identity, marketing_products):
        _LOG.info("Check if consumer identity <%s> is allowed to access marketing products: %s" % \
                  (identity, marketing_products))
        return marketing_products, []

    def record_usage(self, identity, consumer_identifier, marketing_products):
        """
        @param identity consumer's identity
        @type identity: str
        @param consumer_identifier means of uniquely identifying different instances with same consumer identity
            an example could be a mac address
        @type consumer_identifier: str
        @param marketing_products: list of marketing products
        @type marketing_products: [entitlement.models.MarketingProduct]
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
        _LOG.info("Request entitlement certificate from external service: %s:%s%s" % \
                  (cp_config["host"], cp_config["port"], cp_config["url"]))
        identity=identity.uuid
        # TODO:  Remove hardcoding of installed_product
        installed_product="37060!Awesome OS Workstation"

        product_info = candlepin_client.get_entitlement(
            host=cp_config["host"], port=cp_config["port"],
            url=cp_config["url"], installed_product=installed_product,
            identity=identity,
            username=cp_config["username"], password=cp_config["password"])
        return product_info

    def __get_candlepin_config_info(self):
        #TODO: Add config class and parse to determine info for how to connect to candlepin
        return {
            "host": "localhost",
            "port": 8080,
            "url": "/candlepin/splice/cert",
            "username": "admin",
            "password": "password",
        }
