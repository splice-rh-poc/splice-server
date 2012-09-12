from tastypie import fields
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from tastypie.bundle import Bundle
from tastypie.exceptions import NotFound
from tastypie.resources import Resource
from tastypie.exceptions import NotFound, BadRequest

from splice.entitlement.checkin import CheckIn
from splice.common import certs

import logging
_LOG = logging.getLogger(__name__)


# What REST APIs do we plan to expose
#
# 1) Consumer checkin API
#       Consumer request:
#           POST /entitlement
#           Params: {
#               "products": ["PRODUCT_CERT_1", "PRODUCT_CERT_2", ....],
#               "consumer_identifier": "MAC_ADDRESS",
#           }
#       Expected Response: {
#           "certs": ["CERT CONTENT", "KEY CONTENT"],
#           "message": "placeholder to communicate error messages"
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

###
#Note:  Adapted an example of how to create a Resource that doesn't use a Model from:
#       https://gist.github.com/794424
###
class Entitlement(object):
    certs = []
    message = "" # Holder for error messages
#
# TODO: Reconsider if PUT makes sense for 'checkin' call to serve an entitlement certificate
#    From server perspective, we are creating a new entitlement certificate
#    From client perspective, we are requesting an entitlement certificate,
#      I feel like the client is asking for the entitlement certificate,
#      opposed to saying "create this object with this data"
#
class EntitlementResource(Resource):
    certs = fields.ListField(attribute='certs')
    message = fields.CharField(attribute='message', null=True)

    class Meta:
        resource_name = 'entitlement'
        object_class = Entitlement
        list_allowed_methods = []
        detail_allowed_methods = ["post", "put"]
        always_return_data = True
        authentication = Authentication()
        authorization = Authorization()

    # To support a 'POST' on a 'detail', we need to override the tastypies 'post_detail' implementation
    # 'tastypie' by default does not implement a post_detail, so we fallback to behavior of a put
    def post_detail(self, request, **kwargs):
        return self.put_detail(request, **kwargs)

    def obj_update(self, bundle, request=None, skip_errors=False, **kwargs):
        try:
            return self.process_checkin(bundle, request, skip_errors, **kwargs)
        except Exception, e:
            _LOG.exception(e)
            raise

    def process_checkin(self, bundle, request, skip_errors, **kwargs):
        if not bundle.data.has_key("products"):
            raise BadRequest("Missing 'products'")
        if not bundle.data.has_key("consumer_identifier"):
            raise BadRequest("Missing 'consumer_identifier'")
        if not bundle.data.has_key("system_facts"):
            raise BadRequest("Missing 'system_facts'")

        minutes = None
        if bundle.data.has_key("minutes"):
            try:
                minutes = int(bundle.data["minutes"])
                if minutes < 1:
                    raise BadRequest("'minutes' with value of '%s' is less than 1" % (minutes))
            except:
                raise BadRequest("Unable to convert 'minutes' with value of '%s' to an integer" % (bundle.data["minutes"]))

        # Read the SSL identity certificate from the SSL request environment variables
        identity_cert = certs.get_client_cert_from_request(request)
        _LOG.info("Using 'identity_cert': %s" % (identity_cert))
        products = bundle.data["products"]
        consumer_identifier = bundle.data["consumer_identifier"]
        system_facts = bundle.data["system_facts"]
        checkin = CheckIn()
        bundle.obj = Entitlement()
        cert_info = checkin.get_entitlement_certificate(identity_cert, consumer_identifier, system_facts, products,
            cert_length_in_min=minutes)
        bundle.obj.certs = cert_info
        # TODO add support for catching exception and returning appropriate error codes
        # currently we just return a 500
        return bundle
