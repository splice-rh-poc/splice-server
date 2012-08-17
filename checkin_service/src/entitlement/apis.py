from tastypie import fields
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from tastypie.bundle import Bundle
from tastypie.exceptions import NotFound
from tastypie.resources import Resource
from tastypie.exceptions import NotFound, BadRequest

import logging
_LOG = logging.getLogger(__name__)


# What REST APIs do we plan to expose
#
# 1) Consumer checkin API
#       Consumer request:
#           GET /entitlement
#           Params: {
#               "consumer_identity": "CERT CONTENTS",
#               "products": ["PRODUCT_CERT_1", "PRODUCT_CERT_2", ....]
#           }
#       Expected Response: {
#           "entitlement_certificate": "CERT CONTENT"
#           }
#
# 2) SpliceServer requests identity of a consumer
#       Request:  GET /identity/{$IDENTITY_UUID}/
#       Params: {
#           "server_id": "ID of the Splice Server"
#           "API_KEY":  "API KEY VALUE"
#           }
#       Expected Response: {
#           "consumer_identity": "UUID"
#           "subscriptions": [{"marketing_product": "uuid", "expiration": "DATE_TIME"}, ...]
#
# 3) SpliceServer uploads reporting data
#       Request:  PUT /usage/
#       Params: {
#            aggregate of reporting data, format TBD
#           }
#

class CheckInLogic(object):
    """
    Placeholder - class will be refactored and moved to a different module after
    we get basic REST functionality working
    Logic for recording a consumers usage and returning an entitlement certificate
    will be implemented here.
    """
    def get_entitlement_certificate(self, identity_cert, products):
        """
        @param identity_cert: str containing X509 certificate, identify of the consumer
        @type identity_cert: str

        @param products: a list of X509 certificates, identifying each product installed on the consumer
        @type products: [str]

        @return: an x509 certificate to be used as an entitlement certificate
        @rtype: str
        """
        _LOG.info("Validate the identity_certificate is signed by the expected CA")
        _LOG.info("Call out to external service, determine marketing products " +
            "associated to passed in engineering products")
        _LOG.info("Check if consumer identity is allowed to access these products")
        _LOG.info("Record usage")
        _LOG.info("Request entitlement certificate")
        return "contents of X509 string for <%s> with products <%s>" % (identity_cert, products)

###
#Note:  Adapted an example of how to create a Resource that doesn't use a Model from:
#       https://gist.github.com/794424
###
class Entitlement(object):
    entitlement_certificate = "" # X509 Certificate data stored as a string
    message = "" # Holder for error messages

#
# TODO: Reconsider if PUT makes sense for 'checkin' call to serve an entitlement certificate
#    From server perspective, we are creating a new entitlement certificate
#    From client perspective, we are requesting an entitlement certificate,
#      I feel like the client is asking for the entitlement certificate,
#      opposed to saying "create this object with this data"
#
class EntitlementResource(Resource):
    entitlement = fields.CharField(attribute='entitlement')
    message = fields.CharField(attribute='message', null=True)
    
    class Meta:
        resource_name = 'entitlement'
        object_class = Entitlement
        list_allowed_methods = []
        detail_allowed_methods = ["put"]
        always_return_data = True
        authentication = Authentication()
        authorization = Authorization()

    def obj_update(self, bundle, request=None, skip_errors=False, **kwargs):
        if not bundle.data.has_key("identity_cert"):
            raise BadRequest("Missing 'identity_cert'")
        if not bundle.data.has_key("products"):
            raise BadRequest("Missing 'products'")
        identity_cert = bundle.data['identity_cert']
        products = bundle.data["products"]
        checkin = CheckInLogic()
        entitlement_cert = checkin.get_entitlement_certificate(identity_cert, products)
        bundle.obj = Entitlement()
        bundle.obj.entitlement = entitlement_cert
        return bundle

